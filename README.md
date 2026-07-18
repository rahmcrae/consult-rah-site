# consult-rah.com

Personal/consulting site for RVH — analytics engineering, data engineering, and creative technology.
Single self-contained static site, no build step, deployed on GitHub Pages with a custom domain.

Design pattern: one-file `index.html`, numbered sections, dark theme, print-to-PDF, copy-email
button.

## Stack

- Plain HTML/CSS/JS — everything lives in `index.html` (no frameworks, no build tools, no npm install).
- Hosted on GitHub Pages.
- Custom domain: `consult-rah.com` (see `CNAME` and `DEPLOYMENT.md`).

## Local preview

From this folder:

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000 in a browser. No build step — editing `index.html` and refreshing is
the whole workflow.

## Files

| File | Purpose |
|---|---|
| `index.html` | The entire site |
| `CNAME` | Tells GitHub Pages to serve this repo at consult-rah.com |
| `robots.txt` | Crawler rules |
| `sitemap.xml` | Single-URL sitemap |
| `CONTENT-NEEDED.md` | Checklist of copy still needed to replace placeholders |
| `DEPLOYMENT.md` | Step-by-step: create the GitHub repo, enable Pages, point DNS |

## Status

Structural scaffold is done. Sections marked with a `[bracketed, italic]` placeholder and an amber
"Confirm..." note still need real content — see `CONTENT-NEEDED.md`.
