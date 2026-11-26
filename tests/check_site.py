#!/usr/bin/env python3
"""Rules the site must keep. Run: python3 tests/check_site.py

Pins what the owner decided: no personal contact details on the public page, every
local link and font resolves, one h1, no placeholder text. Each rule names why it exists.
"""
from __future__ import annotations

import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "index.html"

# The owner does not want these on the public page (decided 2026-11-26).
BANNED = {
    "a UK mobile number": r"(?<!\d)(?:\+44|0044|07)\s?\d[\d\s-]{8,}",
    "a tel: link": r"\btel:",
    "a mailto: link": r"\bmailto:",
    "an e-mail address": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "a home town": r"Edinburgh|Nottingham,|Naples",
    "citizenship": r"British [Cc]itizen",
    "a placeholder": r"lorem ipsum|TODO|\[[A-Za-z ]+\]|href=\"#\"",
}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self.h1 = 0
        self.external_without_rel: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        for key in ("href", "src"):
            if key in a and a[key]:
                self.links.append((tag, a[key]))
        href = a.get("href", "") or ""
        if tag == "a" and href.startswith("http") and "noopener" not in (a.get("rel") or ""):
            self.external_without_rel.append(href)


def main() -> int:
    text = PAGE.read_text(encoding="utf-8")
    bad: list[str] = []

    for why, pat in BANNED.items():
        # The JSON-LD block and fonts have no such strings; the whole file is scanned.
        if re.search(pat, text):
            bad.append(f"index.html contains {why}")

    p = Page()
    p.feed(text)
    if p.h1 != 1:
        bad.append(f"expected one h1, found {p.h1}")
    for tag, target in p.links:
        if target.startswith(("http://", "https://")):
            if target.startswith("http://"):
                bad.append(f"insecure link: {target}")
            continue
        if target.startswith("#"):
            if target[1:] not in p.ids:
                bad.append(f"anchor {target} has no matching id")
            continue
        if not (ROOT / target.split("?")[0]).exists():
            bad.append(f"{tag} points at a missing file: {target}")
    for href in p.external_without_rel:
        bad.append(f"external link without rel=noopener: {href}")

    for need in ('<link rel="canonical"', 'name="description"', "<title>"):
        if need not in text:
            bad.append(f"missing {need}")
    for f in ("robots.txt", "sitemap.xml", "assets/site.css", "assets/site.js"):
        if not (ROOT / f).exists():
            bad.append(f"missing file {f}")
    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    for font in re.findall(r'url\("([^"]+\.woff2)"\)', css):
        if not (ROOT / "assets" / font).exists():
            bad.append(f"font missing: assets/{font}")
    if "fonts.googleapis.com" in text + css:
        bad.append("fonts must be self-hosted, not loaded from Google")

    if bad:
        print("site check FAILED:\n  " + "\n  ".join(bad))
        return 1
    print("site check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
