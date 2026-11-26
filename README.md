<div align="center">

<img src="docs/assets/brand/icon.svg" width="120" alt="The DC monogram: two white letters on a dark rounded square">

# 🧑‍💻 Davide Caputo Website

**The personal portfolio of Davide Caputo, senior technical architect, as one static page**

![HTML](https://img.shields.io/badge/HTML-static-E34F26?logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS-no%20framework-1572B6?logo=css3&logoColor=white)
![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-222222?logo=github&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## ✨ Features

| | Feature | What it does |
|---|---|---|
| 🎯 | One page | Focus areas, experience, achievements, GitHub projects, skills and certifications. |
| 🔒 | No contact details | No phone, e-mail address or home town. Visitors reach me through LinkedIn. |
| 📱 | Responsive | One column at 390 px, a menu sheet on phones and tablets. |
| 🚫 | Nothing to track you | No cookies, analytics or third-party requests. Fonts are served from this repository. |
| 🧪 | Rules that stay true | `tests/check_site.py` fails if a phone number, e-mail address or broken link appears. |

---

## 🗺️ Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/architecture-dark.svg">
  <img src="docs/assets/architecture-light.svg" width="100%" alt="A visitor's browser asks davidecaputo.com, which Cloudflare DNS points at GitHub Pages; Pages serves the static HTML, CSS and self-hosted fonts from this repository.">
</picture>

The site is one HTML file, one stylesheet, one small script that opens the phone menu, and two font files.

---

## 🚀 Quick Start

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/>. Before a pull request:

```bash
python3 tests/check_site.py
python3 tools/gen_diagram.py --check
```

---

## 📁 Repo structure

```text
Davide-Caputo-Website/
├── index.html          # 🏠 the whole page
├── assets/             # 🎨 site.css, site.js, favicon, self-hosted fonts
├── docs/assets/        # 🖼️ icon and architecture diagram
├── tests/              # 🧪 check_site.py
├── tools/              # 🔧 gen_diagram.py
├── .github/            # 🤖 CI and Dependabot
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
