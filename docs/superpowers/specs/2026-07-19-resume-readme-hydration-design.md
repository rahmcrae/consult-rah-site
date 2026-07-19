# Resume README hydration — design

## Problem

`README.md` is currently repo documentation (stack, local preview, file table). We want it to
instead read as a resume/CV, in the spirit of a reference personal-site repo where the README
mirrors the site's content. Unlike that reference (which hand-maintains README and the site in
lockstep), we want a single versioned source we edit, with the README regenerated from it
automatically — so content updates don't require manually reformatting markdown by hand.

`index.html` (the live site) is explicitly out of scope for this round: it stays hand-edited.
Because two places will describe the same person, agents and the human editor must be told to
keep them in sync manually when either changes.

`CONTENT-NEEDED.md` currently serves as the "what copy do you still owe" checklist for
`index.html`. It is superseded by `resume.yaml`: empty/placeholder fields in `resume.yaml` become
the new checklist, so `CONTENT-NEEDED.md` is deleted.

## Architecture

```
resume.yaml                              ← hand-edited source of truth, versioned
    │
    ▼  scripts/generate_readme.py (Python, uv-managed)
    │
    ▼
README.md                                ← generated output, also committed
```

A git pre-commit hook regenerates `README.md` whenever `resume.yaml` is staged, and adds the
regenerated file to the same commit — so `README.md` is never out of sync with `resume.yaml` in
any commit that touches the source.

## `resume.yaml` schema

Section order mirrors the reference site's README layout:

```yaml
name: ""
title: ""
summary: ""             # 1-2 sentence positioning statement
location: ""
contact:
  linkedin: ""
  email: ""
at_a_glance: []          # short highlight strings
core_expertise: []       # skill/technology tags
experience:
  - company: ""
    title: ""
    dates: ""
    bullets: []
projects:
  - name: ""
    url: ""
    description: ""
education: []
languages:
  - name: ""
    level: ""
tech_stack: []
```

Any empty string or empty list renders as a `_TODO_` marker in the generated README instead of
being silently omitted, so unfinished sections stay visible.

## Generator (`scripts/generate_readme.py`)

Plain Python. Reads `resume.yaml`, renders each section into markdown via string templates, and
writes `README.md`. Dependency: `pyyaml` (stdlib has no YAML parser — the one tradeoff of choosing
YAML as the source format over JSON/TOML, accepted because YAML is meaningfully easier to
hand-edit for this content shape).

Managed via `uv` + `pyproject.toml` per this workspace's Python convention (`uv venv`, `uv sync`,
lockfile committed).

Failure modes:
- `resume.yaml` missing → raise, non-zero exit, no README write.
- `resume.yaml` present but invalid YAML → raise with the parse error, non-zero exit, no README
  write.
- `resume.yaml` valid but missing expected top-level keys → treat as empty/absent for that field
  (renders `_TODO_`), does not raise. Only structurally-broken input (not-a-mapping, wrong types
  for list fields) raises.

The generated `README.md` includes a trailing meta section (mirroring the reference site's
"Repository" footer) with CI/coverage/vulnerability badges and a one-line note: *generated from
`resume.yaml` — do not hand-edit*.

## Pre-commit hook (`hooks/pre-commit`)

Plain shell, versioned in-repo (not just in the untracked `.git/hooks/`). One-time setup:
`git config core.hooksPath hooks`, documented in this repo's `CLAUDE.md`.

Behavior:
- `resume.yaml` in the staged diff → run `uv run scripts/generate_readme.py`, `git add README.md`,
  proceed with commit.
- `resume.yaml` not staged → no-op, proceed with commit.
- Generator exits non-zero → abort the commit, surface the generator's error message.

The hook's shell logic (stage check, dispatch, abort-on-error) is simple enough that it's verified
by manual testing (stage a change, commit, confirm regeneration + abort-on-bad-input) rather than
an automated test harness — the substantive logic lives in the Python generator, which is
unit-tested.

## Testing

`pyproject.toml` dev dependencies: `pytest`, `pytest-cov`. Test file:
`tests/test_generate_readme.py`, table-driven via `@pytest.mark.parametrize` where cases are
similar shapes of the same scenario.

Cases:
- Fully populated `resume.yaml` → every section renders real content, no `_TODO_` markers present.
- Empty/missing fields → corresponding sections render `_TODO_`, script completes successfully.
- Mixed partial data → per-field mix of real content and `_TODO_`, no cross-contamination between
  fields.
- Malformed YAML (parse error) → generator raises, **no** `README.md` write occurs (verify the
  file is untouched, not partially overwritten).
- Missing `resume.yaml` file → generator raises a clear, actionable error.

Target: `pytest --cov --cov-fail-under=100`. The generator is pure (one file read, one file
write, deterministic templating, no network/branching on external state), so full coverage is
achievable without contorting the implementation to hit it.

## CI (new for this repo)

This is a deliberate, explicit exception to the root `CLAUDE.md` guidance to prefer local
workflows over CI/CD — added because the user wants coverage and dependency-vulnerability signal
on a resume-facing repo, which requires a hosted service integration.

`.github/workflows/ci.yml`, triggered on push and pull_request:
1. `uv sync`
2. `uv run pytest --cov --cov-report=xml --cov-fail-under=100`
3. Upload coverage via `codecov/codecov-action` (no token required — repo is public)
4. Dependency vulnerability scan via `snyk/actions/python`, requires a `SNYK_TOKEN` repository
   secret

### Manual setup steps (human-only, cannot be automated by an agent)

1. Connect `rahmcrae/consult-rah-site` at snyk.io and add the resulting token as a GitHub Actions
   repository secret named `SNYK_TOKEN`. CI's Snyk step will fail until this exists.
2. Optional: connect the repo at codecov.io for a `CODECOV_TOKEN` if higher upload rate limits are
   ever needed. Not required for the badge/upload to work on a public repo.

## Badges

Generated README's trailing meta section includes: CI status badge, Codecov coverage badge, Snyk
vulnerability badge, and the "generated from `resume.yaml`" note. Badge URLs reference the
`rahmcrae/consult-rah-site` repo slug directly (this is the user's own public repo, not sensitive).

## Out of scope

- Driving `index.html` content from `resume.yaml`. Explicitly deferred; `CLAUDE.md` will note the
  two must be kept in sync by hand.
- Automated testing of the pre-commit hook shell script itself.
- Any CI auto-commit-back behavior (e.g. a bot committing regenerated README on push) — hydration
  only happens locally via the pre-commit hook, matching the "git pre-commit hook, not GitHub
  Action" decision.
