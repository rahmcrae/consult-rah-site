# consult-rah-site

Personal/consulting static site at consult-rah.com. Defers to the root `.claude/CLAUDE.md` at `_repos/` for process and shared rules.

**Stack:** Single self-contained `index.html` — no framework, no build step, no npm install. Hosted on GitHub Pages with a custom domain (see `CNAME`, `DEPLOYMENT.md`).

**Local preview:** `python3 -m http.server 8000` from this folder, then open `localhost:8000`. Editing `index.html` and refreshing is the whole workflow.

**Status:** Structural scaffold is done; several sections still have `[bracketed, italic]` placeholder copy — see `CONTENT-NEEDED.md` for the exact list before assuming a section is finished.

**Relevant root skills:** `git-workflow` only — no language-specific skill applies to plain HTML/CSS/JS with no build step.
