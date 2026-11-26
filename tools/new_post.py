#!/usr/bin/env python3
"""Start a new blog post: python3 tools/new_post.py "Post title"

Creates content/posts/<today>-<slug>.md with the front matter and a short template,
prints the path, and refuses to overwrite an existing file. Then run
python3 tools/build_site.py to see it.
"""
from __future__ import annotations

import datetime
import pathlib
import re
import sys
import unicodedata

POSTS = pathlib.Path(__file__).resolve().parents[1] / "content" / "posts"

TEMPLATE = """---
title: {title}
summary: One or two plain sentences that say what the post is about.
tags: example, another
# draft: true
---

Write the post here. Leave a blank line between paragraphs.

## A heading

- a bullet
- another bullet

Use `inline code`, **bold**, *italic* and [a link](https://example.com).
"""


def slugify(title: str) -> str:
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main(argv: list[str]) -> int:
    title = " ".join(a for a in argv if not a.startswith("-")).strip()
    if not title or len(argv) != 1 or argv[0].startswith("-"):
        print('usage: python3 tools/new_post.py "Post title"', file=sys.stderr)
        return 2
    slug = slugify(title)
    if not slug:
        print("error: the title needs at least one letter or digit", file=sys.stderr)
        return 2
    path = POSTS / f"{datetime.date.today().isoformat()}-{slug}.md"
    if path.exists():
        print(f"error: {path} already exists, not overwriting", file=sys.stderr)
        return 1
    POSTS.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.format(title=title), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
