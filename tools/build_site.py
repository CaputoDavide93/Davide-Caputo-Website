#!/usr/bin/env python3
"""Build the static site: every html page, the search index and the sitemap.

  python3 tools/build_site.py          # write the generated files
  python3 tools/build_site.py --check  # exit 1 if any generated file is stale (for CI)

Content lives in tools/site_data.py. assets/site.css, assets/site.js, assets/theme.js,
assets/og.png and robots.txt are hand-written or drawn separately and not touched here.
Posts are read from content/posts/YYYY-MM-DD-slug.md (see content/posts/README.md).
The output is deterministic: no build date, no random ordering.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import sys
from html import escape

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from site_data import ABOUT, ACHIEVEMENTS, CERTS, EDU, PROJECTS, ROLES, SKILLS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://davidecaputo.com"
LINKEDIN = "https://www.linkedin.com/in/davidecaputo93"
GITHUB = "https://github.com/CaputoDavide93"
GH = GITHUB + "/"
NAME = "Davide Caputo"
JOB = "Senior Technical Architect"
ORG_LINE = "HM Revenue and Customs, over 10 years in identity and cloud"
HOME_DESC = ("Davide Caputo is a Senior Technical Architect at HM Revenue and Customs with over 10 years "
             "in identity, endpoint management, cloud and automation.")
OG_IMAGE = SITE + "/assets/og.png"
OG_ALT = "Davide Caputo, Senior Technical Architect"
INDEX_TEXT_CAP = 6000

NAV = [("work.html", "Work"), ("about.html", "About"), ("blog/index.html", "Blog"), ("projects.html", "Projects")]
PAGES_META = {
    "work.html": ("Work", "Roles and selected achievements"),
    "about.html": ("About", "Background, skills and certifications"),
    "blog/index.html": ("Blog", "Posts about the tools I build"),
    "projects.html": ("Projects", "Tools and projects on GitHub"),
}
KEYS = [
    ("/", "Search"), ("Cmd or Ctrl + K", "Search"), ("Up, Down, Home, End", "Move through results"),
    ("Page Up, Page Down", "Jump five results"), ("Enter", "Open the result"),
    ("Cmd or Ctrl + Enter", "Open in a new tab"), ("g then w, a, b or p", "Go to Work, About, Blog or Projects"),
    ("t", "Change theme"), ("?", "This list"), ("Esc", "Clear the search or close"),
]

e = escape


def fmt_date(d: str) -> str:
    y, m, dd = (int(x) for x in d.split("-"))
    return f"{dd} {datetime.date(y, m, dd).strftime('%b')} {y}"


def short(s: str, n: int = 157) -> str:
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",;:. ") + "…"


def title_for(t: str) -> str:
    full = f"{t} | {NAME}"
    return full if len(full) <= 60 else t


# ---------------------------------------------------------------- posts from markdown

POSTS_DIR = ROOT / "content" / "posts"
FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
FRONT_KEYS = {"title", "summary", "tags", "draft"}
INLINE_RE = re.compile(r"`([^`\n]+)`|\[([^\]\n]+)\]\(([^)\s]+)\)|\*\*(.+?)\*\*|\*([^*\s][^*]*?)\*", re.S)


class PostError(Exception):
    pass


def fail(name: str, line: int, msg: str):
    raise PostError(f"content/posts/{name}:{line}: {msg}")


def check_url(url: str, name: str, line: int) -> str:
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", url)
    if m and m.group(1).lower() not in ("http", "https"):
        fail(name, line, f"unsafe link scheme '{m.group(1)}:' (only http, https and relative links are allowed)")
    if url.startswith("//"):
        fail(name, line, "protocol-relative links are not allowed; use https://")
    return url


def inline(text: str, name: str, line: int) -> str:
    """Escape everything, then render `code`, [text](url), **bold** and *italic*."""
    out, pos = [], 0
    for m in INLINE_RE.finditer(text):
        out.append(e(text[pos:m.start()]))
        ln = line + text.count("\n", 0, m.start())
        if m.group(1) is not None:
            out.append(f"<code>{e(m.group(1))}</code>")
        elif m.group(3) is not None:
            url = check_url(m.group(3), name, ln)
            rel = ' rel="noopener"' if re.match(r"^https?:", url, re.I) else ""
            out.append(f'<a href="{e(url)}"{rel}>{inline(m.group(2), name, ln)}</a>')
        elif m.group(4) is not None:
            out.append(f"<strong>{inline(m.group(4), name, ln)}</strong>")
        else:
            out.append(f"<em>{inline(m.group(5), name, ln)}</em>")
        pos = m.end()
    out.append(e(text[pos:]))
    return "".join(out)


def plain(text: str) -> str:
    """Markdown inline text to plain words, for the search index."""
    text = re.sub(r"\[([^\]]+)\]\([^)\s]+\)", r"\1", text)
    return re.sub(r"[`*]", "", text)


def parse_blocks(lines: list[str], first: int, name: str) -> list[tuple]:
    """Markdown to blocks: (kind, payload, line). Kinds: p h2 h3 ul ol code quote."""
    blocks, i, n = [], 0, len(lines)
    while i < n:
        raw = lines[i]
        ln = first + i
        if not raw.strip():
            i += 1
        elif raw.startswith("```"):
            lang = raw[3:].strip()
            if lang and not re.fullmatch(r"[A-Za-z0-9+#._-]+", lang):
                fail(name, ln, "bad code fence language")
            j = i + 1
            while j < n and not lines[j].startswith("```"):
                j += 1
            if j >= n:
                fail(name, ln, "code fence is never closed")
            blocks.append(("code", (lang, "\n".join(lines[i + 1:j])), ln))
            i = j + 1
        elif re.match(r"^#{1,6}(\s|$)", raw):
            m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", raw)
            if not m or len(m.group(1)) not in (2, 3):
                fail(name, ln, "headings must be ## or ### (the title is the page heading)")
            blocks.append(("h" + str(len(m.group(1))), m.group(2), ln))
            i += 1
        elif re.match(r"^[-*] +\S", raw) or re.match(r"^\d+[.)] +\S", raw):
            kind = "ul" if raw[0] in "-*" else "ol"
            pat = r"^[-*] +(.*)$" if kind == "ul" else r"^\d+[.)] +(.*)$"
            items = []
            while i < n and re.match(pat, lines[i]):
                items.append([re.match(pat, lines[i]).group(1).strip(), first + i])
                i += 1
                while i < n and lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]):
                    items[-1][0] += " " + lines[i].strip()
                    i += 1
            blocks.append((kind, items, ln))
        elif raw.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            blocks.append(("quote", " ".join(buf), ln))
        else:
            buf = []
            while i < n and lines[i].strip() and not re.match(r"^(```|#{1,6}(\s|$)|[-*] +\S|\d+[.)] +\S|>)", lines[i]):
                buf.append(lines[i].strip())
                i += 1
            blocks.append(("p", " ".join(buf), ln))
    return blocks


def load_post(path: pathlib.Path) -> dict | None:
    name = path.name
    m = FILE_RE.match(name)
    if not m:
        fail(name, 1, "file name must be YYYY-MM-DD-slug.md (lowercase letters, digits and hyphens)")
    date, slug = m.groups()
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        fail(name, 1, f"'{date}' is not a real date")
    lines = path.read_bytes().decode("utf-8").replace("\r\n", "\n").splitlines()
    if not lines or lines[0].strip() != "---":
        fail(name, 1, "the file must start with a front matter block: a line of ---")
    end = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), None)
    if end is None:
        fail(name, 1, "front matter is never closed with a line of ---")
    meta: dict[str, str] = {}
    for k in range(1, end):
        if not lines[k].strip() or lines[k].lstrip().startswith("#"):
            continue
        key, sep, val = lines[k].partition(":")
        key = key.strip().lower()
        if not sep or key not in FRONT_KEYS:
            fail(name, k + 1, f"unknown front matter line (allowed keys: {', '.join(sorted(FRONT_KEYS))})")
        meta[key] = val.strip().strip("\"'") if val.strip()[:1] in "\"'" else val.strip()
    if not meta.get("title"):
        fail(name, 1, "title: is missing or empty")
    if not meta.get("summary"):
        fail(name, 1, "summary: is missing or empty")
    draft = meta.get("draft", "false").lower()
    if draft not in ("true", "false"):
        fail(name, 1, "draft: must be true or false")
    if draft == "true":
        return None
    tags = [t.strip().lower() for t in meta.get("tags", "").split(",") if t.strip()]
    body = parse_blocks(lines[end + 1:], end + 2, name)
    for kind, payload, ln in body:  # fail early on unsafe links, naming the line
        if kind in ("p", "h2", "h3", "quote"):
            inline(payload, name, ln)
        elif kind in ("ul", "ol"):
            for text, iln in payload:
                inline(text, name, iln)
    return dict(slug=slug, title=meta["title"], date=date, summary=meta["summary"], tags=tags, body=body, file=name)


def load_posts() -> list[dict]:
    posts, seen = [], {}
    for path in sorted(POSTS_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        post = load_post(path)
        if post is None:
            continue
        if post["slug"] in seen:
            fail(path.name, 1, f"slug '{post['slug']}' is already used by {seen[post['slug']]}")
        seen[post["slug"]] = path.name
        posts.append(post)
    return sorted(posts, key=lambda p: (p["date"], p["slug"]), reverse=True)


try:
    POSTS = load_posts()
except PostError as err:
    print(f"error: {err}", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------- search index

def post_text(p: dict) -> str:
    out = [p["summary"]]
    for kind, payload, _ in p["body"]:
        if kind == "code":
            out.append(payload[1])
        elif kind in ("ul", "ol"):
            out.extend(plain(t) for t, _ in payload)
        else:
            out.append(plain(payload))
    return " ".join(" ".join(out).split())[:INDEX_TEXT_CAP]


def build_index() -> tuple[list[dict], list]:
    idx: list[dict] = []
    page_tags = {
        "work.html": sorted({r["org"].lower() for r in ROLES}) + ["cv", "experience", "career", "achievements"],
        "about.html": ["skills", "certifications", "education", "contact"],
        "blog/index.html": ["posts", "writing"],
        "projects.html": ["github", "code", "tools"],
    }
    icons = {"work.html": "W", "about.html": "A", "blog/index.html": "B", "projects.html": "Pr"}
    for url, (t, sub) in PAGES_META.items():
        idx.append(dict(type="page", title=t, sub=sub, url=url, ext=False, tags=page_tags[url], text="", icon=icons[url]))
    idx.append(dict(type="link", title="Contact on LinkedIn", sub="Architecture, identity or security", url=LINKEDIN,
                    ext=True, tags=["linkedin", "contact"], text="", icon="in"))
    idx.append(dict(type="link", title="See my GitHub", sub="The code behind these projects", url=GITHUB,
                    ext=True, tags=["github", "code"], text="", icon="gh"))
    for p in POSTS:
        idx.append(dict(type="post", title=p["title"], sub=p["summary"], url=f"blog/{p['slug']}.html", ext=False,
                        tags=p["tags"], text=post_text(p), icon="bl"))
    for p in PROJECTS:
        idx.append(dict(type="project", title=p["title"], sub=p["blurb"], url=GH + p["repo"], ext=True,
                        tags=p["tags"], text=f"{p['repo']} {p['lang']} {p['blurb']}", icon="{}"))
    first_post = [i for i, x in enumerate(idx) if x["type"] == "post"][:1]
    projects = [i for i, x in enumerate(idx) if x["type"] == "project"][:3]
    defaults = [["Pages", [0, 1, 2, 3]], ["Get in touch", [4, 5]], ["Latest", first_post + projects]]
    return idx, defaults


def index_js(idx: list[dict], defaults: list) -> str:
    rows = ",\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in idx)
    return ("/* Generated by tools/build_site.py. Do not edit. */\n"
            f"window.SEARCH_INDEX=[\n{rows}\n];\n"
            f"window.SEARCH_DEFAULTS={json.dumps(defaults)};\n")


# ---------------------------------------------------------------- shared html

def row_html(it: dict, root: str, rid: str, selected: bool) -> str:
    url = it["url"] if it["ext"] else root + it["url"]
    rel = ' rel="noopener"' if it["ext"] else ""
    return (f'<a class="row" role="option" id="{rid}" href="{e(url)}"{rel} aria-selected="{"true" if selected else "false"}">'
            f'<i class="ic" aria-hidden="true">{e(it["icon"])}</i>'
            f'<span class="t"><b>{e(it["title"])}</b><span class="s">{e(it["sub"])}</span></span>'
            f'<kbd class="kh">enter</kbd></a>')


def groups_html(idx: list[dict], defaults: list, root: str, idp: str, only: list[str] | None = None) -> str:
    out, n = [], 0
    for gi, (name, ids) in enumerate(defaults):
        if only and name not in only:
            continue
        rows = []
        for i in ids:
            rows.append(row_html(idx[i], root, f"{idp}-r{n}", n == 0))
            n += 1
        out.append(f'<div role="group" aria-labelledby="{idp}-g{gi}"><div class="gh" id="{idp}-g{gi}">{e(name)}</div>'
                   + "".join(rows) + "</div>")
    return "".join(out)


SEARCH_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
              'aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>')
THEME_SVG = ('<svg class="i-system" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>'
             '<svg class="i-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/></svg>'
             '<svg class="i-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/></svg>')


def theme_btn() -> str:
    return (f'<button class="tbtn" type="button" data-theme-toggle aria-label="Theme: System. Switch to Light.">'
            f'{THEME_SVG}<span class="tl-label" data-theme-label>System</span></button>')


def palette(idx, defaults, root, idp, body_groups="", only=None, extra_class="") -> str:
    inner = body_groups if body_groups else groups_html(idx, defaults, root, idp, only)
    own = ' data-defaults="Pages"' if only else ""
    return (
        f'<div class="q" role="search" aria-label="Site search">{SEARCH_SVG}'
        f'<input type="search" id="{idp}-in" role="combobox" aria-expanded="true" aria-controls="{idp}-list" '
        f'aria-activedescendant="{idp}-r0" aria-autocomplete="list" aria-label="Search posts and projects" '
        f'placeholder="Search posts and projects" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="search">'
        f'<button class="esc" type="button" data-clear aria-label="Clear search">esc</button></div>'
        f'<div class="res" tabindex="-1"{own}><div class="list" id="{idp}-list" role="listbox" aria-label="Results">{inner}</div>'
        f'<p class="empty" data-empty hidden></p></div>'
        f'<p class="sr" role="status" aria-live="polite" data-live></p>'
    )


def band_html() -> str:
    return (f'<footer class="band"><div class="who"><a class="role" href="work.html" data-root-href="work.html">{JOB}</a>'
            f'<span>{ORG_LINE}</span></div><div class="band-r"><button class="kbtn" type="button" data-open-help>Keyboard</button>'
            f'{theme_btn()}</div></footer>')


def band_inner(root: str) -> str:
    return band_html().replace('href="work.html" data-root-href="work.html"', f'href="{root}work.html"')


def help_html() -> str:
    keys = "".join(f"<div><dt><kbd>{e(k)}</kbd></dt><dd>{e(d)}</dd></div>" for k, d in KEYS)
    return (f'<div class="ov" id="help-ov" hidden><div class="cp help" role="dialog" aria-modal="true" aria-labelledby="help-h">'
            f'<div class="hb"><h2 id="help-h">Keyboard</h2><button class="esc" type="button" data-close aria-label="Close keyboard help">esc</button></div>'
            f'<dl class="keys">{keys}</dl></div></div>')


def overlay_html(idx, defaults, root) -> str:
    return (
        f'<div class="ov" id="search-ov" hidden><div class="cp" role="dialog" aria-modal="true" aria-label="Search" '
        f'data-palette data-overlay data-idp="o" data-root="{root}">{palette(idx, defaults, root, "o", body_groups=" ")}'
        f'<div class="hints"><span><kbd>↑</kbd> <kbd>↓</kbd> to move</span><span><kbd>enter</kbd> to open</span>'
        f'<span><kbd>esc</kbd> to close</span></div></div></div>' + help_html()
    )


def head(path: str, root: str, title: str, desc: str, ld: list[dict] | None = None, noindex: bool = False) -> str:
    canon = SITE + "/" + ("" if path == "index.html" else path)
    ttl = e(title)
    ds = e(desc)
    out = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        f"<title>{ttl}</title>",
        f'<meta name="description" content="{ds}">',
        '<meta name="robots" content="noindex">' if noindex else '<meta name="robots" content="index,follow">',
        '<meta name="color-scheme" content="light dark">',
        '<meta name="theme-color" content="#ffb4d2" media="(prefers-color-scheme: light)">',
        '<meta name="theme-color" content="#140d18" media="(prefers-color-scheme: dark)">',
        f'<link rel="canonical" href="{canon}">' if not noindex else "",
        f'<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">',
        f'<meta property="og:type" content="{"article" if path.startswith("blog/") and path != "blog/index.html" else "website"}">',
        f'<meta property="og:site_name" content="{NAME}">',
        f'<meta property="og:title" content="{ttl}">',
        f'<meta property="og:description" content="{ds}">',
        f'<meta property="og:url" content="{canon}">',
        f'<meta property="og:image" content="{OG_IMAGE}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{OG_ALT}">',
        '<meta property="og:locale" content="en_GB">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{ttl}">',
        f'<meta name="twitter:description" content="{ds}">',
        f'<meta name="twitter:image" content="{OG_IMAGE}">',
        f'<link rel="preload" href="{root}assets/fonts/host-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>',
        f'<script src="{root}assets/theme.js"></script>',
        f'<link rel="stylesheet" href="{root}assets/site.css">',
        f'<script src="{root}assets/search-index.js" defer></script>',
        f'<script src="{root}assets/site.js" defer></script>',
    ]
    for block in ld or []:
        out.append('<script type="application/ld+json">\n' + json.dumps(block, ensure_ascii=False, separators=(",", ":")) + "\n</script>")
    return "\n".join(x for x in out if x)


def shell(path, root, title, desc, body, ld=None, noindex=False, body_class="") -> str:
    return (
        f'<!doctype html>\n<html lang="en-GB">\n<head>\n{head(path, root, title, desc, ld, noindex)}\n</head>\n'
        f'<body class="{body_class}" data-root="{root}">\n'
        f'<div id="page">\n<a class="skip" href="#main">Skip to content</a>\n{body}\n</div>\n'
        f'{{OVERLAYS}}\n</body>\n</html>\n'
    )


def breadcrumbs(items: list[tuple[str, str]]) -> dict:
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + "/" + u} for i, (n, u) in enumerate(items)]}


def inner_page(path, title, h1, desc, content, idx, defaults, ld_extra=None, crumbs=None, nav_current=None) -> str:
    root = "../" * path.count("/")
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{root}{u}"{cur if u == nav_current else ""}>{n}</a>' for u, n in NAV)
    top = (
        f'<header class="top"><a class="home" href="{root}index.html">{NAME}</a>'
        f'<div class="tools"><button class="sbtn" type="button" data-open-search aria-haspopup="dialog">'
        f'{SEARCH_SVG}<span>Search</span><kbd class="kh">/</kbd></button></div>'
        f'<nav class="pills" aria-label="Main">{nav}</nav></header>'
    )
    body = (f'{top}\n<div class="card"><main id="main" class="body" tabindex="-1">\n<h1>{e(h1)}</h1>\n{content}\n</main>\n'
            f'{band_inner(root)}</div>')
    ld = [breadcrumbs(crumbs or [("Home", ""), (h1, path)])] + (ld_extra or [])
    html = shell(path, root, title, desc, body, ld)
    return html.replace("{OVERLAYS}", overlay_html(idx, defaults, root))


# ---------------------------------------------------------------- pages

def home(idx, defaults) -> str:
    person = {"@context": "https://schema.org", "@type": "Person", "name": NAME, "jobTitle": JOB,
              "worksFor": {"@type": "Organization", "name": "HM Revenue and Customs"}, "url": SITE + "/",
              "sameAs": [GITHUB, LINKEDIN]}
    body = (
        f'<main id="main" class="home" tabindex="-1"><h1 class="sr">{NAME}, {JOB}</h1>\n'
        f'<div class="cp" data-palette data-idp="h">{palette(idx, defaults, "", "h")}{band_html()}</div></main>'
    )
    html = shell("index.html", "", f"{NAME}, {JOB}", HOME_DESC, body, [person], body_class="is-home")
    return html.replace("{OVERLAYS}", help_html())


def not_found(idx, defaults) -> str:
    body = (
        f'<main id="main" class="home" tabindex="-1">\n'
        f'<div class="cp" data-palette data-idp="h" data-notfound><div class="nf"><h1>Page not found</h1>'
        f'<p>That address does not exist here. Pick a page or search for a post or project.</p></div>'
        f'{palette(idx, defaults, "/", "h", only=["Pages"])}'
        f'{band_html().replace("href=" + chr(34) + "work.html" + chr(34), "href=" + chr(34) + "/work.html" + chr(34))}</div></main>'
    )
    html = shell("404.html", "/", "Page not found | " + NAME, "This page does not exist. Use the links to find Work, About, Blog or Projects.",
                 body, None, noindex=True, body_class="is-home")
    return html.replace("{OVERLAYS}", help_html())


def work(idx, defaults) -> str:
    roles = "".join(
        f'<li><span class="when">{e(r["when"])}</span><div><h3>{e(r["title"])}</h3><p class="org">{e(r["org"])}</p>'
        + (f'<p>{e(r["detail"])}</p>' if r["detail"] else "") + "</div></li>" for r in ROLES)
    ach = "".join(f"<li><strong>{e(b)}</strong>{e(r)}</li>" for b, r in ACHIEVEMENTS)
    content = f'<h2>Roles</h2><ol class="tl">{roles}</ol>\n<h2>Selected achievements</h2><ul class="ach">{ach}</ul>'
    return inner_page("work.html", title_for("Work"), "Work",
                      "Davide Caputo's work history: Senior Technical Architect at HM Revenue and Customs, and the roles and achievements before it.",
                      content, idx, defaults, nav_current="work.html")


def about(idx, defaults) -> str:
    paras = "".join(f"<p>{e(p)}</p>" for p in ABOUT)
    skills = "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in SKILLS)
    certs = "".join(f'<li><span>{e(n)}</span><span class="when">{e(w)}</span></li>' for n, w in CERTS)
    edu = "".join(f"<li>{e(x)}</li>" for x in EDU)
    content = (
        f'<div class="prose">{paras}</div>\n<h2>Skills</h2><dl class="skills">{skills}</dl>\n'
        f'<h2>Certifications</h2><ul class="certs">{certs}</ul>\n<h2>Education</h2><ul class="plain">{edu}</ul>\n'
        f'<h2>Get in touch</h2><div class="btns"><a class="btn btn-primary" href="{LINKEDIN}" rel="noopener">Contact on LinkedIn</a>'
        f'<a class="btn btn-secondary" href="{GITHUB}" rel="noopener">See my GitHub</a></div>'
    )
    return inner_page("about.html", title_for("About"), "About",
                      "About Davide Caputo: his background, skills and certifications in identity, endpoint management, cloud and automation.",
                      content, idx, defaults, nav_current="about.html")


def blog_index(idx, defaults) -> str:
    items = "".join(
        f'<li><article><time datetime="{p["date"]}">{fmt_date(p["date"])}</time><h2><a href="{p["slug"]}.html">{e(p["title"])}</a></h2>'
        f'<p>{e(p["summary"])}</p><ul class="chips" aria-label="Tags">{"".join(f"<li>{e(t)}</li>" for t in p["tags"])}</ul></article></li>'
        for p in POSTS)
    content = f'<ul class="posts">{items}</ul>' if POSTS else "<p>No posts yet.</p>"
    lst = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Blog", "url": SITE + "/blog/index.html",
           "mainEntity": {"@type": "ItemList", "itemListElement": [
               {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/blog/{p['slug']}.html", "name": p["title"]}
               for i, p in enumerate(POSTS)]}}
    return inner_page("blog/index.html", title_for("Blog"), "Blog",
                      "Posts by Davide Caputo about the tools he builds for identity, endpoint management and cloud work.",
                      content, idx, defaults, [lst], nav_current="blog/index.html")


def render_body(blocks, name: str) -> str:
    out = []
    for kind, val, ln in blocks:
        if kind == "p":
            out.append(f"<p>{inline(val, name, ln)}</p>")
        elif kind in ("h2", "h3"):
            out.append(f"<{kind}>{inline(val, name, ln)}</{kind}>")
        elif kind in ("ul", "ol"):
            out.append(f"<{kind}>" + "".join(f"<li>{inline(t, name, l)}</li>" for t, l in val) + f"</{kind}>")
        elif kind == "code":
            lang, text = val
            cls = f' class="language-{e(lang)}"' if lang else ""
            out.append(f'<pre tabindex="0"><code{cls}>{e(text)}</code></pre>')
        elif kind == "quote":
            out.append(f"<blockquote><p>{inline(val, name, ln)}</p></blockquote>")
    return "\n".join(out)


def post_page(p, idx, defaults) -> str:
    chips = "".join(f"<li>{e(t)}</li>" for t in p["tags"])
    content = (f'<p class="back"><a href="index.html">← All posts</a></p>'
               f'<p class="meta"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time></p>'
               f'<ul class="chips" aria-label="Tags">{chips}</ul>\n<div class="prose post">{render_body(p["body"], p["file"])}</div>\n'
               f'<p class="back"><a href="index.html">← All posts</a></p>')
    path = f"blog/{p['slug']}.html"
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "datePublished": p["date"],
          "author": {"@type": "Person", "name": NAME, "url": SITE + "/"}, "description": p["summary"],
          "keywords": ", ".join(p["tags"]), "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE}/{path}"}}
    crumbs = [("Home", ""), ("Blog", "blog/index.html"), (p["title"], path)]
    return inner_page(path, title_for(p["title"]), p["title"], short(p["summary"]), content, idx, defaults, [ld],
                      crumbs, nav_current="blog/index.html")


def projects_page(idx, defaults) -> str:
    def card(p):
        return (f'<li><a class="proj" href="{GH}{e(p["repo"])}" rel="noopener"><h3>{e(p["title"])}</h3><p>{e(p["blurb"])}</p>'
                f'<span class="meta"><span>{e(p["lang"])}</span><span>{e(p["repo"])}</span></span></a></li>')
    parts = []
    for grp, heading in (("work", "Built for work"), ("home", "Built at home")):
        items = [p for p in PROJECTS if p["group"] == grp]
        if items:
            parts.append(f'<h2>{heading}</h2><ul class="grid">{"".join(card(p) for p in items)}</ul>')
    lst = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Projects", "url": SITE + "/projects.html",
           "mainEntity": {"@type": "ItemList", "itemListElement": [
               {"@type": "ListItem", "position": i + 1, "url": GH + p["repo"], "name": p["title"]} for i, p in enumerate(PROJECTS)]}}
    return inner_page("projects.html", title_for("Projects"), "Projects",
                      "Public tools and projects by Davide Caputo on GitHub, from device management and AWS audits to Home Assistant integrations.",
                      "\n".join(parts), idx, defaults, [lst], nav_current="projects.html")


def sitemap() -> str:
    newest = max((p["date"] for p in POSTS), default=None)
    urls = [("", newest), ("work.html", None), ("about.html", None), ("blog/index.html", newest), ("projects.html", None)]
    urls += [(f"blog/{p['slug']}.html", p["date"]) for p in POSTS]
    rows = "".join(f"  <url><loc>{SITE}/{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n" for u, d in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + rows + "</urlset>\n")


def generate() -> dict[str, str]:
    idx, defaults = build_index()
    out = {
        "index.html": home(idx, defaults), "404.html": not_found(idx, defaults), "work.html": work(idx, defaults),
        "about.html": about(idx, defaults), "projects.html": projects_page(idx, defaults),
        "blog/index.html": blog_index(idx, defaults), "assets/search-index.js": index_js(idx, defaults),
        "sitemap.xml": sitemap(),
    }
    for p in POSTS:
        out[f"blog/{p['slug']}.html"] = post_page(p, idx, defaults)
    return out


def main() -> int:
    try:
        files = generate()
    except PostError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    check = "--check" in sys.argv[1:]
    stale = []
    for rel, text in sorted(files.items()):
        path = ROOT / rel
        current = path.read_bytes().decode("utf-8") if path.exists() else None
        if current != text:
            stale.append(rel)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(text.encode("utf-8"))
    if check:
        for rel in stale:
            print(f"stale: {rel}")
        print("site is up to date" if not stale else "run: python3 tools/build_site.py")
        return 1 if stale else 0
    print(f"wrote {len(stale)} of {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
