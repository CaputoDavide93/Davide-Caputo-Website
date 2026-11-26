# Posts

Each post is one file here, named `YYYY-MM-DD-slug.md`. The date and the address come from the file name.

## Post from GitHub

1. Open [github.com/CaputoDavide93/Davide-Caputo-Website/new/main/content/posts](https://github.com/CaputoDavide93/Davide-Caputo-Website/new/main/content/posts).
2. Name the file `YYYY-MM-DD-slug.md`, add the front matter below, and write the post under it.
3. Commit to `main`. The publish workflow rebuilds the pages from the file.

## Or write it locally (optional)

Run `python3 tools/new_post.py "Post title"` to create the file, then preview with `python3 tools/build_site.py && python3 -m http.server 8000` and commit the file together with the regenerated `blog/`, `assets/search-index.js` and `sitemap.xml`.

## Front matter

```
---
title: What the post is called
summary: One or two plain sentences, shown in lists and search.
tags: jamf, macos
draft: true
---
```

`title` and `summary` are required. `tags` is a comma list. `draft: true` hides the post everywhere until you remove the line.

## Markdown you can use

Paragraphs, `##` and `###` headings, bullet (`-`) and numbered (`1.`) lists, fenced code blocks (three backticks, optional language), `inline code`, `**bold**`, `*italic*`, `[links](https://example.com)` (http, https or relative only) and `>` block quotes. Raw HTML is shown as text, never run.
