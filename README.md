<div align="center">

<img src="docs/assets/brand/icon.svg" width="120" alt="The DC monogram: two white letters on a dark rounded square">

# 🧑‍💻 Davide Caputo Website

**The personal portfolio of Davide Caputo, senior technical architect, as a small static site with a command palette**

![HTML](https://img.shields.io/badge/HTML-static-E34F26?logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS-no%20framework-1572B6?logo=css3&logoColor=white)
![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-222222?logo=github&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## ✨ Features

| | Feature | What it does |
|---|---|---|
| ⌨️ | Command-palette home | A search box over the pages, the blog posts and my GitHub projects. It runs in the browser over a static index. |
| 💼 | Work, About, Blog, Projects | Work holds the CV history. The inner pages share a header, a nav and the search overlay. |
| 🌗 | Light and dark | Follows the system setting, with a toggle on every page. |
| 🔒 | No contact details | No phone, e-mail address or home town. Visitors reach me through LinkedIn. |
| 🚫 | Nothing to track you | No cookies, analytics or third-party requests. Fonts are served from this repository. |
| 🧪 | Rules that stay true | `tests/check_site.py` fails when a rule below is broken. |

### What the checks guarantee

- No phone number, e-mail address, `mailto:`/`tel:` link, home town or placeholder text, on any page or in the search index.
- Every local link, anchor and font resolves; external links use https with `rel="noopener"`; nothing loads from another host.
- Every page has one `h1`, a unique title and description, a canonical URL, Open Graph and Twitter tags, and valid JSON-LD of the right type.
- The sitemap lists the pages that exist and nothing else; `404.html` is `noindex` and not listed. Every page and post is in the search index.
- Keyboard access: a skip link first on every page, a `main` landmark, `aria-current` on the nav, named buttons, image `alt` and size, no positive `tabindex`.
- Dark theme: light tokens on `:root`, dark tokens under `prefers-color-scheme` and `[data-theme="dark"]`, theme colour for both schemes, a toggle with a name, and no hard-coded colours outside the tokens.
- Size budgets for the stylesheet, scripts, search index, social image and each page.

---

## 🗺️ Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/architecture-dark.svg">
  <img src="docs/assets/architecture-light.svg" width="100%" alt="A visitor's browser asks davidecaputo.com, which Cloudflare DNS points at GitHub Pages; Pages serves the static HTML, CSS and self-hosted fonts from this repository.">
</picture>

The pages are generated: `tools/site_data.py` holds the content and `tools/build_site.py` writes the HTML, `sitemap.xml` and the search index. The browser gets static files, one stylesheet, two small scripts (search, and the theme) and two font files.

---

## 🚀 Quick Start

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/>. Content lives in `tools/site_data.py`; after editing it, regenerate the pages:

```bash
python3 tools/build_site.py
```

Before a pull request:

```bash
python3 tools/build_site.py --check
python3 tests/check_site.py
python3 tools/gen_diagram.py --check
```

---

## ✍️ Write a blog post

### On GitHub (the usual way)

1. Open the [new file page](https://github.com/CaputoDavide93/Davide-Caputo-Website/new/main/content/posts).
2. Name the file `YYYY-MM-DD-slug.md`, for example `2026-12-01-my-post.md`. The date is the publish date; the slug becomes the page address.
3. Paste this block, fill it in, and write the post under it:

```markdown
---
title: Your title
summary: One sentence, under 160 characters.
tags: one, two
---

Write the post here.
```

4. Commit to `main`. The `Publish` workflow (`.github/workflows/publish.yml`) runs `python3 tools/build_site.py` and commits the rebuilt pages as `github-actions[bot]`, and the site updates. Nothing needs installing.

Front matter fields: `title` and `summary` are required, `tags` is a list, and `draft: true` keeps the post out of the pages, the sitemap and the search index until the line is removed.

The post body is Markdown. The generator reads it with its own small converter, so only what `tools/build_site.py` supports is rendered; check the post page after it publishes.

### Locally (optional)

```bash
python3 tools/new_post.py "Your title"   # creates content/posts/YYYY-MM-DD-your-title.md
# edit the file
python3 tools/build_site.py
# preview with python3 -m http.server 8000, then commit the .md and the generated files
```

The generated HTML is never edited by hand: `python3 tools/build_site.py --check` fails on it.

---

## 📁 Repo structure

```text
Davide-Caputo-Website/
├── index.html  work.html  about.html  projects.html  404.html   # 🏠 generated pages
├── blog/               # 📝 generated blog index and posts
├── content/posts/      # ✍️ blog posts as Markdown (the source)
├── assets/             # 🎨 site.css, site.js, theme.js, search-index.js, og.png, favicon, self-hosted fonts
├── docs/assets/        # 🖼️ icon and architecture diagram
├── tests/              # 🧪 check_site.py
├── tools/              # 🔧 build_site.py, site_data.py, new_post.py, gen_diagram.py
├── .github/            # 🤖 CI, publish workflow and Dependabot
├── AGENTS.md           # 🤖 agent instructions
├── LICENSE  SECURITY.md  README.md
├── robots.txt  sitemap.xml  .nojekyll
└── .gitignore
```

---

## 🔒 Security

Report a problem through a [private security advisory](https://github.com/CaputoDavide93/Davide-Caputo-Website/security/advisories/new). See [SECURITY.md](SECURITY.md).

---

## 📄 License

Code is [MIT](LICENSE). The text of the CV content is © Davide Caputo.

---

<p align="center"><sub>Made with ❤️ by <a href="https://github.com/CaputoDavide93">Davide Caputo</a></sub></p>
