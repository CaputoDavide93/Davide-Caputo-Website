#!/usr/bin/env python3
"""Rules the site must keep. Run: python3 tests/check_site.py

Pins what the owner decided: no personal contact details anywhere on the public site,
every local link and font resolves, one h1 per page, no placeholder text, no third-party
requests, a sitemap and a search index that match the pages that exist. Each rule says
why it exists.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://davidecaputo.com"
SKIP_DIRS = {"docs", "node_modules", ".git", ".github"}

# The owner does not want these on the public site (decided 2026-11-26).
BANNED = {
    "a UK mobile number": r"(?<!\d)(?:\+44|0044|07)\s?\d[\d\s-]{8,}",
    "a tel: link": r"\btel:",
    "a mailto: link": r"\bmailto:",
    "an e-mail address": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "a home town": r"Edinburgh|Nottingham,|Naples",
    "citizenship": r"British [Cc]itizen",
    "a placeholder": r"lorem ipsum|TODO|\[[A-Za-z ]+\]|href=\"#\"",
}


def pages() -> list[pathlib.Path]:
    """Every html file in the repo outside docs/ and node_modules."""
    out = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or any(part.startswith(".") for part in rel.parts):
            continue
        out.append(p)
    return out


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str, str, str]] = []  # tag, attr, value, rel
        self.h1 = 0
        self.lang = ""
        self.canonical = ""
        self.description = ""
        self.has_title = False
        self.inline_handlers: list[str] = []
        self.external_a_without_rel: list[str] = []
        self._in_title = False
        self.title = ""
        self.metas: dict[str, str] = {}
        self.jsonld: list[str] = []
        self._in_ld = False
        self.first_focusable: tuple[str, dict] | None = None
        self.main_ids: set[str] = set()
        self.aria_current = 0
        self.imgs: list[dict] = []
        self.unnamed_buttons = 0
        self._buttons: list[dict] = []
        self.bad_tabindex: list[str] = []
        self.theme_colors: list[str] = []
        self.blocking_scripts: list[tuple[str, bool]] = []  # (src, in head)
        self.theme_buttons = 0
        self.theme_buttons_unnamed = 0
        self._in_head = False

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "head":
            self._in_head = True
        if tag == "body":
            self._in_head = False
        if tag == "meta" and a.get("name") == "theme-color":
            self.theme_colors.append(a.get("media", ""))
        if tag == "script" and a.get("type") != "application/ld+json" and a.get("src"):
            if "defer" not in a and "async" not in a and a.get("type") != "module":
                self.blocking_scripts.append((a["src"], self._in_head))
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.has_title = True
            self._in_title = True
        if tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.metas[key] = a.get("content", "")
            if a.get("name") == "description":
                self.description = a.get("content", "")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self.jsonld.append("")
        if tag == "main" and a.get("id"):
            self.main_ids.add(a["id"])
        if "aria-current" in a:
            self.aria_current += 1
        if tag == "img":
            self.imgs.append(a)
        ti = a.get("tabindex", "")
        if re.fullmatch(r"\d+", ti) and int(ti) > 0:
            self.bad_tabindex.append(f"<{tag} tabindex={ti}>")
        focusable = (
            (tag == "a" and "href" in a)
            or tag in ("button", "select", "textarea", "summary")
            or (tag == "input" and a.get("type") != "hidden")
            or (re.fullmatch(r"-?\d+", ti) and int(ti) >= 0)
        )
        if focusable and "disabled" not in a and self.first_focusable is None:
            self.first_focusable = (tag, a)
        if tag == "button":
            self._buttons.append(
                {
                    "named": bool(a.get("aria-label") or a.get("aria-labelledby") or a.get("title")),
                    "text": "",
                    "theme": "theme" in " ".join([a.get("id", ""), a.get("class", ""), a.get("aria-label", ""), *(k for k in a if k.startswith("data-"))]).lower(),
                }
            )
        if tag == "img" and self._buttons and a.get("alt"):
            self._buttons[-1]["text"] += a["alt"]
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        for k in a:
            if k.startswith("on"):
                self.inline_handlers.append(f"<{tag} {k}=...>")
        for key in ("href", "src", "srcset", "action"):
            if a.get(key):
                self.refs.append((tag, key, a[key], a.get("rel", "")))
        href = a.get("href", "")
        if tag == "a" and href.startswith("http") and "noopener" not in a.get("rel", ""):
            self.external_a_without_rel.append(href)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script":
            self._in_ld = False
        if tag == "button" and self._buttons:
            b = self._buttons.pop()
            named = b["named"] or bool(b["text"].strip())
            if not named:
                self.unnamed_buttons += 1
            if b["theme"]:
                self.theme_buttons += 1
                self.theme_buttons_unnamed += 0 if named else 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld and self.jsonld:
            self.jsonld[-1] += data
        if self._buttons:
            self._buttons[-1]["text"] += data


def resolve(page: pathlib.Path, target: str) -> pathlib.Path:
    """Map a local href/src to a file; a directory means its index.html."""
    path = urlsplit(target).path
    base = ROOT if path.startswith("/") else page.parent
    f = (base / path.lstrip("/")).resolve()
    if path == "" or path.endswith("/") or f.is_dir():
        f = f / "index.html"
    return f


def page_url(page: pathlib.Path) -> set[str]:
    """Canonical URLs a page may declare: its path, or the directory form for index.html."""
    rel = page.relative_to(ROOT).as_posix()
    urls = {f"{SITE}/{rel}"}
    if rel == "index.html":
        urls.add(f"{SITE}/")
    elif rel.endswith("/index.html"):
        urls.add(f"{SITE}/{rel[: -len('index.html')]}")
    return urls


def norm_local(url: str) -> str:
    """Normalise a search-index url to a repo-relative file path."""
    path = urlsplit(url).path.lstrip("/")
    if path.startswith("./"):
        path = path[2:]
    if path == "" or path.endswith("/"):
        path += "index.html"
    return path


def search_entries(text: str) -> list[dict]:
    """Parse the JSON assigned to window.SEARCH_INDEX."""
    m = re.search(r"window\.SEARCH_INDEX\s*=\s*", text)
    if not m:
        raise ValueError("assets/search-index.js does not assign window.SEARCH_INDEX")
    data, _ = json.JSONDecoder().raw_decode(text[m.end():])
    if isinstance(data, dict):
        data = [v for v in data.values() if isinstance(v, list) for v in v] or list(data.values())
    return [e for e in data if isinstance(e, dict)]


def ld_types(blocks: list[str], rel: str, bad: list[str]) -> tuple[set[str], list[dict]]:
    """Parse JSON-LD blocks; return the @type values and the nodes."""
    types: set[str] = set()
    nodes: list[dict] = []

    def walk(x):
        if isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, dict):
            nodes.append(x)
            t = x.get("@type")
            for v in ([t] if isinstance(t, str) else t or []):
                types.add(v)
            walk(x.get("@graph", []))

    for b in blocks:
        try:
            walk(json.loads(b))
        except json.JSONDecodeError as e:
            # Invalid JSON-LD is ignored by search engines, silently.
            bad.append(f"{rel}: JSON-LD does not parse: {e}")
    return types, nodes


def size_budget(path: pathlib.Path, limit: int, bad: list[str]) -> None:
    """Weight budgets keep the site fast on a phone."""
    if path.exists() and path.stat().st_size > limit:
        bad.append(f"{path.relative_to(ROOT).as_posix()} is {path.stat().st_size} bytes, budget {limit}")


def main() -> int:
    bad: list[str] = []
    files = pages()
    parsed: dict[pathlib.Path, Page] = {}
    titles: dict[str, list[str]] = {}
    descs: dict[str, list[str]] = {}

    if not files:
        bad.append("no html pages found")

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        p = Page()
        p.feed(text)
        parsed[f] = p

        for why, pat in BANNED.items():
            # The whole file is scanned, JSON-LD included.
            if re.search(pat, text):
                bad.append(f"{rel} contains {why}")

        # One h1 so every page has a single clear subject.
        if p.h1 != 1:
            bad.append(f"{rel}: expected one h1, found {p.h1}")
        # Search results and tabs need a title and description on every page.
        if not p.has_title or not p.title.strip():
            bad.append(f"{rel}: missing <title>")
        if not p.description.strip():
            bad.append(f"{rel}: missing meta description")
        # Screen readers and hyphenation need the document language.
        if not p.lang:
            bad.append(f"{rel}: missing lang attribute on <html>")
        # A wrong canonical points search engines at the wrong page.
        if "noindex" not in p.metas.get("robots", "") and p.canonical not in page_url(f):
            bad.append(f"{rel}: canonical {p.canonical!r} should be one of {sorted(page_url(f))}")
        # Inline handlers break the no-inline-script rule and block a strict CSP.
        for h in p.inline_handlers:
            bad.append(f"{rel}: inline event handler {h}")

        indexable = "noindex" not in p.metas.get("robots", "")
        if rel == "404.html" and indexable:
            # An indexable error page would be listed in search results.
            bad.append("404.html must carry <meta name=robots content=noindex>")
        # Long titles and descriptions are cut off in search results.
        if len(p.title.strip()) >= 60:
            bad.append(f"{rel}: title is {len(p.title.strip())} characters, limit 59")
        if len(p.description) >= 160:
            bad.append(f"{rel}: description is {len(p.description)} characters, limit 159")
        # Pages with the same title or description compete with each other in search.
        titles.setdefault(p.title.strip(), []).append(rel)
        descs.setdefault(p.description.strip(), []).append(rel)
        # Page weight budget.
        size_budget(f, 60 * 1024, bad)

        if indexable:
            # Link previews need Open Graph and Twitter tags that agree with the canonical.
            for key in ("og:title", "og:description", "og:image", "og:url", "twitter:card"):
                if not p.metas.get(key, "").strip():
                    bad.append(f"{rel}: missing {key}")
            if p.metas.get("og:url") and p.metas["og:url"] != p.canonical:
                bad.append(f"{rel}: og:url differs from canonical")
            img = p.metas.get("og:image", "")
            if img:
                local = img[len(SITE):] if img.startswith(SITE) else img
                if img.startswith("http") and not img.startswith(SITE):
                    bad.append(f"{rel}: og:image is hosted elsewhere: {img}")
                elif not (ROOT / local.lstrip("/")).exists():
                    bad.append(f"{rel}: og:image file is missing: {img}")
            # Structured data per page kind drives rich results and breadcrumbs.
            types, nodes = ld_types(p.jsonld, rel, bad)
            if rel == "index.html":
                want = "Person"
            elif re.fullmatch(r"blog/(?!index\.html)[^/]+\.html", rel):
                want = "BlogPosting"
            else:
                want = "BreadcrumbList"
            if want not in types:
                bad.append(f"{rel}: JSON-LD should include @type {want}, found {sorted(types)}")
            if want == "BlogPosting" and not any(n.get("@type") == "BlogPosting" and n.get("datePublished") for n in nodes):
                bad.append(f"{rel}: BlogPosting has no datePublished")

        # Keyboard users need a skip link first and a main landmark to land on.
        ff = p.first_focusable
        target = (ff[1].get("href", "") if ff and ff[0] == "a" else "")
        if not (target.startswith("#") and target[1:] in p.main_ids):
            bad.append(f"{rel}: the first focusable element must be a skip link to <main id=...>")
        if not p.main_ids:
            bad.append(f"{rel}: missing <main id=...>")
        # Screen readers announce the current page from aria-current.
        # The home page and the error page have no nav to mark.
        if rel not in ("404.html", "index.html") and p.aria_current == 0:
            bad.append(f"{rel}: nav does not mark the current page with aria-current")
        # Images need alt text and a size so the layout does not jump.
        for im in p.imgs:
            if "alt" not in im:
                bad.append(f"{rel}: image without alt: {im.get('src', '')}")
            if not (im.get("width") and im.get("height")):
                bad.append(f"{rel}: image without width and height: {im.get('src', '')}")
        # A button with no name is announced as just "button".
        if p.unnamed_buttons:
            bad.append(f"{rel}: {p.unnamed_buttons} button(s) without an accessible name")
        # Dark theme: the browser UI colour must follow both schemes, and the toggle must exist.
        media = " ".join(p.theme_colors)
        if len(p.theme_colors) < 2 or "dark" not in media or "light" not in media:
            bad.append(f"{rel}: needs <meta name=theme-color> for both prefers-color-scheme: light and dark")
        if p.theme_buttons == 0:
            bad.append(f"{rel}: missing a theme toggle button")
        elif p.theme_buttons_unnamed:
            bad.append(f"{rel}: theme toggle button has no accessible name")
        # The only blocking script allowed is the tiny theme script in <head>, so the page never flashes the wrong theme.
        for src, in_head in p.blocking_scripts:
            if src.split("?")[0].lstrip("./").lstrip("/").endswith("assets/theme.js"):
                if not in_head:
                    bad.append(f"{rel}: assets/theme.js must be loaded in <head>")
            else:
                bad.append(f"{rel}: blocking script {src} (only assets/theme.js may block; use defer)")
        if not any(s_.split("?")[0].endswith("assets/theme.js") for s_, _ in p.blocking_scripts):
            bad.append(f"{rel}: assets/theme.js is not loaded as a blocking script in <head>")
        # Positive tabindex breaks the natural focus order.
        for t in p.bad_tabindex:
            bad.append(f"{rel}: {t} (tabindex above 0)")

        for tag, key, target, rel_attr in p.refs:
            if target.startswith("http://"):
                # Plain http can be tampered with in transit.
                bad.append(f"{rel}: insecure link: {target}")
            elif target.startswith("https://"):
                is_nav = tag == "a"
                is_meta = tag == "link" and rel_attr in ("canonical", "alternate")
                if not is_nav and not is_meta:
                    # No third-party requests: scripts, styles, fonts, images stay local.
                    bad.append(f"{rel}: external {tag} {key} loads from another host: {target}")
            elif target.startswith(("javascript:", "data:")):
                if target.startswith("javascript:"):
                    bad.append(f"{rel}: javascript: link")
            elif target.startswith(("mailto:", "tel:")):
                pass  # reported by the banned list
            else:
                # Every local link must resolve, or visitors land on a 404.
                dest = resolve(f, target)
                if not dest.exists():
                    bad.append(f"{rel}: {tag} points at a missing file: {target}")
                    continue
                frag = urlsplit(target).fragment
                if frag and dest.suffix == ".html":
                    ids = p.ids if dest == f else None
                    if ids is None:
                        if dest not in parsed:
                            q = Page()
                            q.feed(dest.read_text(encoding="utf-8"))
                            parsed[dest] = q
                        ids = parsed[dest].ids
                    # An anchor without an id scrolls nowhere.
                    if frag not in ids:
                        bad.append(f"{rel}: anchor {target} has no matching id")
        # External links must not leak the opener window.
        for href in p.external_a_without_rel:
            bad.append(f"{rel}: external link without rel=noopener: {href}")

        # A bare "#" or a dangling "#frag" on this page: covered above via resolve("").

    for t, who in titles.items():
        if len(who) > 1:
            bad.append(f"same title on {', '.join(who)}: {t!r}")
    for d, who in descs.items():
        if len(who) > 1:
            bad.append(f"same description on {', '.join(who)}")
    for name, limit in (("assets/site.css", 20), ("assets/site.js", 16), ("assets/search-index.js", 60), ("assets/og.png", 200)):
        size_budget(ROOT / name, limit * 1024, bad)
    # Link previews need the image the og:image tags point at.
    if not (ROOT / "assets" / "og.png").exists():
        bad.append("missing file assets/og.png")
    # A custom 404 page keeps visitors on the site, and must stay out of the sitemap.
    if not (ROOT / "404.html").exists():
        bad.append("missing file 404.html")

    # Fonts and styles: files exist and nothing is loaded from Google.
    css_path = ROOT / "assets" / "site.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    if not css_path.exists():
        bad.append("missing file assets/site.css")
    for font in re.findall(r'url\("?([^")]+\.woff2)"?\)', css):
        # A missing font file silently falls back to a system font.
        if not (css_path.parent / font).resolve().exists():
            bad.append(f"font missing: assets/{font}")
    # Self-hosted fonts keep visitor IP addresses away from Google.
    for f in files:
        if "fonts.googleapis.com" in f.read_text(encoding="utf-8"):
            bad.append(f"{f.relative_to(ROOT).as_posix()}: fonts must be self-hosted, not loaded from Google")
    if "fonts.googleapis.com" in css:
        bad.append("assets/site.css: fonts must be self-hosted, not loaded from Google")
    # No third-party requests from the stylesheet either.
    if re.search(r"(?:url\(\s*|@import\s+)[\"']?https?:", css):
        bad.append("assets/site.css loads something from another host")

    # Dark theme lives in tokens: light on :root, dark under the media query and the toggle attribute.
    if css:
        if not re.search(r":root\s*\{", css):
            bad.append("assets/site.css has no light tokens on :root")
        if not re.search(r"prefers-color-scheme:\s*dark", css):
            bad.append("assets/site.css has no dark tokens under prefers-color-scheme")
        if not re.search(r'\[data-theme=["\']?dark["\']?\]', css):
            bad.append('assets/site.css has no dark tokens under [data-theme="dark"]')
        # Colours belong in the token blocks only, so both themes stay in step.
        rest = css
        while True:
            m = re.search(r'(?::root|\[data-theme)[^{}]*\{', rest)
            if not m:
                break
            depth, i = 1, m.end()
            while i < len(rest) and depth:
                depth += {"{": 1, "}": -1}.get(rest[i], 0)
                i += 1
            rest = rest[: m.start()] + rest[i:]
        rest = re.sub(r"/\*.*?\*/", "", rest, flags=re.S)
        stray = sorted(set(re.findall(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(", rest)))
        if stray:
            bad.append(f"assets/site.css has hard-coded colours outside the token blocks: {', '.join(stray[:8])}")

    # The theme script runs before first paint on every page: it must stay tiny and inert.
    th = ROOT / "assets" / "theme.js"
    if not th.exists():
        bad.append("missing file assets/theme.js")
    else:
        tt = th.read_text(encoding="utf-8")
        if th.stat().st_size >= 400:
            bad.append(f"assets/theme.js is {th.stat().st_size} bytes, budget under 400")
        for needle in ("eval(", "document.write", "fetch(", "XMLHttpRequest", "WebSocket", "http:", "https:", "import(", "sendBeacon"):
            if needle in tt:
                bad.append(f"assets/theme.js contains {needle}")

    # Posts: the Markdown sources are the truth, the pages are generated from them.
    posts_dir = ROOT / "content" / "posts"
    sources = sorted(m for m in posts_dir.glob("*.md") if m.name != "README.md") if posts_dir.exists() else []
    drafts: set[str] = set()
    slugs: set[str] = set()
    for md in sources:
        mrel = md.relative_to(ROOT).as_posix()
        mm = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md", md.name)
        # The filename carries the publish date and the page address.
        if not mm:
            bad.append(f"{mrel}: file name must be YYYY-MM-DD-slug.md (lowercase, hyphens)")
            continue
        try:
            datetime.date(int(mm[1]), int(mm[2]), int(mm[3]))
        except ValueError:
            bad.append(f"{mrel}: the date in the file name is not a real date")
        mtext = md.read_text(encoding="utf-8")
        fm = re.match(r"---\s*\n(.*?)\n---\s*\n", mtext, re.S)
        front = {}
        if not fm:
            bad.append(f"{mrel}: missing front matter")
        else:
            for line in fm[1].splitlines():
                k, _, v = line.partition(":")
                front[k.strip()] = v.strip().strip("\"'")
        if not front.get("title"):
            bad.append(f"{mrel}: front matter needs a title")
        summ = front.get("summary", "")
        if not summ:
            bad.append(f"{mrel}: front matter needs a summary")
        elif len(summ) >= 160:
            bad.append(f"{mrel}: summary is {len(summ)} characters, limit 159")
        # A post body is public the moment it is built: the same banned list applies.
        for why, pat in BANNED.items():
            if re.search(pat, mtext):
                bad.append(f"{mrel} contains {why}")
        if front.get("draft", "").lower() == "true":
            drafts.add(mm[4])
        slugs.add(mm[4])
    # Every generated blog page needs a Markdown source, or it cannot be rebuilt.
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        mp = re.fullmatch(r"blog/(?!index\.html)([^/]+)\.html", rel)
        if mp and mp[1] not in slugs:
            bad.append(f"{rel} has no matching content/posts/*-{mp[1]}.md source")
        if mp and mp[1] in drafts:
            bad.append(f"{rel} is generated from a draft post")
    # A draft must not leak into the sitemap or the search index.
    for slug in drafts:
        for name in ("sitemap.xml", "assets/search-index.js"):
            fp = ROOT / name
            if fp.exists() and f"blog/{slug}" in fp.read_text(encoding="utf-8"):
                bad.append(f"{name} lists the draft post {slug}")

    # robots.txt is how crawlers find the sitemap.
    if not (ROOT / "robots.txt").exists():
        bad.append("missing file robots.txt")

    # The sitemap lists exactly the pages that exist, so nothing 404s and nothing is hidden.
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        bad.append("missing file sitemap.xml")
    else:
        locs = set(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm.read_text(encoding="utf-8")))
        wanted = {parsed[f].canonical for f in files if "noindex" not in parsed[f].metas.get("robots", "") and parsed[f].canonical}
        for loc in sorted(locs - wanted):
            bad.append(f"sitemap.xml lists {loc}, which is not a page's canonical url")
        for loc in sorted(wanted - locs):
            bad.append(f"sitemap.xml is missing {loc}")

    # The search index is the data behind the search box: banned content, dead urls and
    # missing pages would all reach visitors.
    si = ROOT / "assets" / "search-index.js"
    if not si.exists():
        bad.append("missing file assets/search-index.js")
    else:
        si_text = si.read_text(encoding="utf-8")
        for why, pat in BANNED.items():
            if re.search(pat, si_text):
                bad.append(f"assets/search-index.js contains {why}")
        try:
            entries = search_entries(si_text)
        except (ValueError, json.JSONDecodeError) as e:
            bad.append(f"assets/search-index.js: {e}")
            entries = []
        indexed: set[str] = set()
        for e in entries:
            url = str(e.get("url", ""))
            if not url:
                bad.append(f"search index entry without a url: {e.get('title', e)!r}")
            elif url.startswith("https://"):
                pass
            elif url.startswith("http://"):
                bad.append(f"search index url is not https: {url}")
            else:
                path = norm_local(url)
                indexed.add(path)
                if not (ROOT / path).exists():
                    bad.append(f"search index points at a missing file: {url}")
        # Every page and post must be findable from the search box.
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            # The home page is the search box itself; the 404 page is noindex.
            if rel == "index.html" or "noindex" in parsed[f].metas.get("robots", ""):
                continue
            if rel not in indexed:
                bad.append(f"search index has no entry for {rel}")

    # The home page must link to the Work page through the owner's title.
    home = ROOT / "index.html"
    if home.exists():
        ph = parsed.get(home)
        txt = home.read_text(encoding="utf-8")
        link_ok = re.search(r'<a\b[^>]*href="(?:\./|/)?work\.html"[^>]*>\s*Senior Technical Architect\s*</a>', txt)
        if not link_ok:
            bad.append('index.html must link to work.html through the text "Senior Technical Architect"')
    else:
        bad.append("missing file index.html")

    # The script runs in every visitor's browser: keep it free of code-injection primitives.
    js = ROOT / "assets" / "site.js"
    if not js.exists():
        bad.append("missing file assets/site.js")
    else:
        js_text = js.read_text(encoding="utf-8")
        for needle in ("eval(", "document.write"):
            if needle in js_text:
                bad.append(f"assets/site.js contains {needle}")

    if bad:
        print("site check FAILED:\n  " + "\n  ".join(bad))
        return 1
    print("site check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
