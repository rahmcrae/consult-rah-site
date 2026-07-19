# Resume README Hydration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `README.md` a resume/CV that's generated from a versioned `resume.yaml`, regenerated automatically on commit, fully test-covered, with CI running Codecov and Snyk.

**Architecture:** `resume.yaml` (hand-edited data) → `scripts/generate_readme.py` (pure templating, uv-managed) → `README.md` (generated, still committed). A `hooks/pre-commit` shell hook regenerates `README.md` and stages it whenever `resume.yaml` is part of a commit. GitHub Actions runs the test suite with 100% coverage enforcement, uploads coverage to Codecov, and scans dependencies with Snyk.

**Tech Stack:** Python 3.11+, `uv` (env/deps), `pyyaml`, `pytest` + `pytest-cov`, plain POSIX shell (hook), GitHub Actions.

## Global Constraints

- Only production dependency is `pyyaml` — no other runtime deps.
- Env/deps managed via `uv` + `pyproject.toml` + committed lockfile (this repo's Python convention).
- Empty or missing `resume.yaml` fields render as the literal marker `_TODO_` in `README.md` — never silently omitted.
- Missing `resume.yaml` file, or a file that fails to parse as YAML, must raise (non-zero exit) and must **not** write `README.md`.
- Coverage gate: `pytest --cov-fail-under=100` (line coverage) must pass.
- Hydration trigger is a **git pre-commit hook** (`hooks/pre-commit` + `git config core.hooksPath hooks`) — explicitly not a GitHub Action that auto-commits.
- CI is a deliberate, explicit exception to this workspace's "prefer local workflows over CI/CD" default, added because the user wants coverage/vulnerability signal on this repo.
- Codecov upload needs no token (repo is public). Snyk needs a `SNYK_TOKEN` repository secret that only the human can create (account/token setup is not automatable).
- `index.html` is out of scope for this work and stays hand-edited; `CLAUDE.md` must carry a reminder that it and `resume.yaml` need manual sync.
- `CONTENT-NEEDED.md` is deleted — `resume.yaml`'s empty/`_TODO_` fields are its replacement.
- Badge URLs use repo slug `rahmcrae/consult-rah-site`.

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `scripts/__init__.py` (empty)
- Create: `resume.yaml`

**Interfaces:**
- Produces: a `uv`-managed environment with `pyyaml` (runtime) and `pytest`, `pytest-cov` (dev) installed, and an importable `scripts` package. Later tasks run `uv run pytest` and `uv run scripts/generate_readme.py` against this environment.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "consult-rah-site-tools"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
addopts = "--cov=scripts --cov-report=term-missing --cov-fail-under=100"
```

- [ ] **Step 2: Create empty `scripts/__init__.py`**

Empty file — makes `scripts` an importable package for `from scripts.generate_readme import ...` in tests.

- [ ] **Step 3: Write `resume.yaml`**

```yaml
name: ""
title: ""
summary: ""
location: ""
contact:
  linkedin: ""
  email: ""
at_a_glance: []
core_expertise: []
experience: []
projects: []
education: []
languages: []
tech_stack: []
```

- [ ] **Step 4: Install the environment**

Run: `uv lock && uv sync`
Expected: completes without error; creates `uv.lock` and `.venv/`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock scripts/__init__.py resume.yaml
git commit -m "Scaffold uv-managed Python tooling and resume.yaml source"
```

---

### Task 2: `load_resume()` — YAML loading and validation

**Files:**
- Create: `scripts/generate_readme.py`
- Create: `tests/test_generate_readme.py`

**Interfaces:**
- Produces: `TODO: str = "_TODO_"` constant; `REPO_SLUG: str = "rahmcrae/consult-rah-site"` constant; `load_resume(path: Path) -> dict` — raises `FileNotFoundError` if `path` doesn't exist, raises `ValueError` if the parsed YAML isn't a mapping, propagates `yaml.YAMLError` on parse failure, otherwise returns the parsed dict. `_text(value: object, default: str = TODO) -> str` — returns `default` if `value` is falsy/blank, else `str(value)`. `_list(value: object) -> list` — returns `[]` if `value` is falsy, else `list(value)`.
- Consumed by: Task 3 onward (renderers use `_text`/`_list`), Task 6 (`main()` uses `load_resume`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_generate_readme.py`:

```python
from pathlib import Path

import pytest
import yaml

from scripts.generate_readme import load_resume


def test_load_resume_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_resume(tmp_path / "resume.yaml")


def test_load_resume_malformed_yaml_raises(tmp_path: Path) -> None:
    path = tmp_path / "resume.yaml"
    path.write_text("name: [unterminated")
    with pytest.raises(yaml.YAMLError):
        load_resume(path)


def test_load_resume_non_mapping_raises(tmp_path: Path) -> None:
    path = tmp_path / "resume.yaml"
    path.write_text("- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="mapping"):
        load_resume(path)


def test_load_resume_valid_returns_dict(tmp_path: Path) -> None:
    path = tmp_path / "resume.yaml"
    path.write_text("name: Rah\n")
    assert load_resume(path) == {"name": "Rah"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_readme.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.generate_readme'` (file doesn't exist yet).

- [ ] **Step 3: Write the minimal implementation**

Create `scripts/generate_readme.py`:

```python
"""Regenerate README.md from resume.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml

TODO = "_TODO_"
REPO_SLUG = "rahmcrae/consult-rah-site"


def load_resume(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found — README.md is generated from it.")
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must parse to a YAML mapping, got {type(data).__name__}")
    return data


def _text(value: object, default: str = TODO) -> str:
    if not value or not str(value).strip():
        return default
    return str(value)


def _list(value: object) -> list:
    if not value:
        return []
    return list(value)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate_readme.py -v`
Expected: 4 passed. (The coverage gate from `addopts` will still report failure at this point since `_text`/`_list` aren't exercised yet — that resolves once every task's tests are in. Confirm the tests themselves are green with: `uv run pytest tests/test_generate_readme.py -v --no-cov`.)

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_readme.py tests/test_generate_readme.py
git commit -m "Add resume.yaml loading and validation"
```

---

### Task 3: Simple section renderers — header, summary, contact, bullet section

**Files:**
- Modify: `scripts/generate_readme.py`
- Modify: `tests/test_generate_readme.py`

**Interfaces:**
- Consumes: `TODO`, `_text`, `_list` from Task 2.
- Produces: `render_header(resume: dict) -> str`, `render_summary(resume: dict) -> str`, `render_contact(resume: dict) -> str`, `render_bullet_section(title: str, items: object) -> str`.
- Consumed by: Task 5 (`render_readme` assembly).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_generate_readme.py` (update the import line to include the new names, and append these):

```python
from scripts.generate_readme import (
    TODO,
    load_resume,
    render_bullet_section,
    render_contact,
    render_header,
    render_summary,
)

FULL_RESUME = {
    "name": "Rah McRae",
    "title": "Analytics Engineer",
    "location": "Remote",
    "summary": "Builds data platforms and full-stack tools.",
    "contact": {"linkedin": "https://linkedin.com/in/example", "email": "rah@example.com"},
}

EMPTY_RESUME: dict = {}


@pytest.mark.parametrize(
    ("resume", "expect_todo"),
    [(FULL_RESUME, False), (EMPTY_RESUME, True)],
)
def test_render_header(resume: dict, expect_todo: bool) -> None:
    assert (TODO in render_header(resume)) is expect_todo


@pytest.mark.parametrize(
    ("resume", "expect_todo"),
    [(FULL_RESUME, False), (EMPTY_RESUME, True)],
)
def test_render_summary(resume: dict, expect_todo: bool) -> None:
    assert (TODO in render_summary(resume)) is expect_todo


@pytest.mark.parametrize(
    ("resume", "expect_todo"),
    [(FULL_RESUME, False), (EMPTY_RESUME, True)],
)
def test_render_contact(resume: dict, expect_todo: bool) -> None:
    assert (TODO in render_contact(resume)) is expect_todo


@pytest.mark.parametrize(
    ("items", "expect_todo"),
    [(["one", "two"], False), ([], True), (None, True)],
)
def test_render_bullet_section(items, expect_todo: bool) -> None:
    result = render_bullet_section("Core Expertise", items)
    assert "## Core Expertise" in result
    assert (TODO in result) is expect_todo
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'render_header'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `scripts/generate_readme.py`:

```python
def render_header(resume: dict) -> str:
    name = _text(resume.get("name"))
    title = _text(resume.get("title"))
    location = _text(resume.get("location"))
    return f"# {name}\n\n**{title}** · {location}\n"


def render_summary(resume: dict) -> str:
    return f"## Summary\n\n{_text(resume.get('summary'))}\n"


def render_contact(resume: dict) -> str:
    contact = resume.get("contact") or {}
    linkedin = _text(contact.get("linkedin"))
    email = _text(contact.get("email"))
    return f"## Contact\n\n- LinkedIn: {linkedin}\n- Email: {email}\n"


def render_bullet_section(title: str, items: object) -> str:
    items = _list(items)
    if not items:
        return f"## {title}\n\n- {TODO}\n"
    body = "\n".join(f"- {item}" for item in items)
    return f"## {title}\n\n{body}\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_readme.py tests/test_generate_readme.py
git commit -m "Add header, summary, contact, and bullet-section renderers"
```

---

### Task 4: Composite renderers — experience, projects, languages

**Files:**
- Modify: `scripts/generate_readme.py`
- Modify: `tests/test_generate_readme.py`

**Interfaces:**
- Consumes: `TODO`, `_text`, `_list` from Task 2.
- Produces: `render_experience(resume: dict) -> str`, `render_projects(resume: dict) -> str`, `render_languages(resume: dict) -> str`.
- Consumed by: Task 5 (`render_readme` assembly).

- [ ] **Step 1: Write the failing tests**

Update the import in `tests/test_generate_readme.py` to add `render_experience, render_projects, render_languages`, and extend `FULL_RESUME` with:

```python
FULL_RESUME.update(
    {
        "experience": [
            {
                "company": "Acme Corp",
                "title": "Senior Analytics Engineer",
                "dates": "2022–Present",
                "bullets": ["Cut pipeline runtime 40%", "Owned the dbt monorepo"],
            }
        ],
        "projects": [
            {
                "name": "trading-agent",
                "url": "https://github.com/rahmcrae/trading-agent",
                "description": "IBKR trading agent",
            }
        ],
        "languages": [{"name": "English", "level": "Native"}],
    }
)
```

Append these tests:

```python
@pytest.mark.parametrize(
    ("resume", "expect_todo"),
    [(FULL_RESUME, False), (EMPTY_RESUME, True)],
)
def test_render_experience(resume: dict, expect_todo: bool) -> None:
    assert (TODO in render_experience(resume)) is expect_todo


def test_render_experience_role_without_bullets() -> None:
    resume = {"experience": [{"company": "Acme", "title": "Eng", "dates": "2020"}]}
    assert TODO in render_experience(resume)


@pytest.mark.parametrize(
    ("resume", "expect_todo"),
    [(FULL_RESUME, False), (EMPTY_RESUME, True)],
)
def test_render_projects(resume: dict, expect_todo: bool) -> None:
    assert (TODO in render_projects(resume)) is expect_todo


def test_render_projects_without_url_omits_link() -> None:
    resume = {"projects": [{"name": "side-project", "description": "A thing"}]}
    result = render_projects(resume)
    assert "[side-project]" not in result
    assert "side-project" in result


@pytest.mark.parametrize(
    ("resume", "expect_todo"),
    [(FULL_RESUME, False), (EMPTY_RESUME, True)],
)
def test_render_languages(resume: dict, expect_todo: bool) -> None:
    assert (TODO in render_languages(resume)) is expect_todo
```

(Remember to add `render_experience, render_projects, render_languages` to the `from scripts.generate_readme import (...)` block at the top of the test file.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'render_experience'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `scripts/generate_readme.py`:

```python
def render_experience(resume: dict) -> str:
    roles = _list(resume.get("experience"))
    if not roles:
        return f"## Experience\n\n- {TODO}\n"
    blocks = []
    for role in roles:
        company = _text(role.get("company"))
        title = _text(role.get("title"))
        dates = _text(role.get("dates"))
        bullets = _list(role.get("bullets"))
        bullet_lines = "\n".join(f"- {b}" for b in bullets) if bullets else f"- {TODO}"
        blocks.append(f"### {title}, {company} ({dates})\n\n{bullet_lines}")
    return "## Experience\n\n" + "\n\n".join(blocks) + "\n"


def render_projects(resume: dict) -> str:
    projects = _list(resume.get("projects"))
    if not projects:
        return f"## Projects\n\n- {TODO}\n"
    lines = []
    for project in projects:
        name = _text(project.get("name"))
        url = project.get("url")
        description = _text(project.get("description"))
        label = f"[{name}]({url})" if url else name
        lines.append(f"- **{label}** — {description}")
    return "## Projects\n\n" + "\n".join(lines) + "\n"


def render_languages(resume: dict) -> str:
    languages = _list(resume.get("languages"))
    if not languages:
        return f"## Languages\n\n- {TODO}\n"
    lines = [f"- {_text(lang.get('name'))} — {_text(lang.get('level'))}" for lang in languages]
    return "## Languages\n\n" + "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_readme.py tests/test_generate_readme.py
git commit -m "Add experience, projects, and languages renderers"
```

---

### Task 5: `render_meta()` and `render_readme()` assembly

**Files:**
- Modify: `scripts/generate_readme.py`
- Modify: `tests/test_generate_readme.py`

**Interfaces:**
- Consumes: `REPO_SLUG`, all `render_*` functions from Tasks 3–4.
- Produces: `render_meta() -> str`, `render_readme(resume: dict) -> str` — assembles every section in order: header, summary, contact, "At a Glance", "Core Expertise", experience, projects, "Education", languages, "Tech Stack", meta.
- Consumed by: Task 6 (`main()`).

- [ ] **Step 1: Write the failing tests**

Update the import in `tests/test_generate_readme.py` to add `render_meta, render_readme`, extend `FULL_RESUME` with the remaining fields:

```python
FULL_RESUME.update(
    {
        "at_a_glance": ["8 years analytics engineering", "Led 3 platform migrations"],
        "core_expertise": ["SQL", "Python", "dbt"],
        "education": ["B.S. Computer Science, Somewhere State"],
        "tech_stack": ["Python", "TypeScript", "AWS"],
    }
)
```

Append these tests:

```python
def test_render_meta_has_badges_and_source_note() -> None:
    result = render_meta()
    assert "codecov.io" in result
    assert "snyk.io" in result
    assert "resume.yaml" in result


def test_render_readme_full_has_no_todo_markers() -> None:
    assert TODO not in render_readme(FULL_RESUME)


def test_render_readme_empty_has_todo_in_every_section() -> None:
    result = render_readme(EMPTY_RESUME)
    for heading in (
        "Summary", "Contact", "At a Glance", "Core Expertise",
        "Experience", "Projects", "Education", "Languages", "Tech Stack",
    ):
        assert f"## {heading}" in result
    assert result.count(TODO) >= 9


def test_render_readme_partial_mixed_content() -> None:
    resume = {"name": "Rah McRae", "core_expertise": ["SQL"]}
    result = render_readme(resume)
    assert "Rah McRae" in result
    assert "SQL" in result
    assert TODO in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'render_meta'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `scripts/generate_readme.py`:

```python
def render_meta() -> str:
    return (
        "## Repository\n\n"
        f"![CI](https://github.com/{REPO_SLUG}/actions/workflows/ci.yml/badge.svg) "
        f"[![codecov](https://codecov.io/gh/{REPO_SLUG}/branch/main/graph/badge.svg)]"
        f"(https://codecov.io/gh/{REPO_SLUG}) "
        f"[![Known Vulnerabilities](https://snyk.io/test/github/{REPO_SLUG}/badge.svg)]"
        f"(https://snyk.io/test/github/{REPO_SLUG})\n\n"
        "This README is generated from `resume.yaml` — do not hand-edit. "
        "Run `uv run scripts/generate_readme.py` after changing `resume.yaml`, "
        "or just commit — the pre-commit hook does it for you. "
        "See `CLAUDE.md` for repo/dev docs.\n"
    )


def render_readme(resume: dict) -> str:
    sections = [
        render_header(resume),
        render_summary(resume),
        render_contact(resume),
        render_bullet_section("At a Glance", resume.get("at_a_glance")),
        render_bullet_section("Core Expertise", resume.get("core_expertise")),
        render_experience(resume),
        render_projects(resume),
        render_bullet_section("Education", resume.get("education")),
        render_languages(resume),
        render_bullet_section("Tech Stack", resume.get("tech_stack")),
        render_meta(),
    ]
    return "\n".join(sections)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: 17 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_readme.py tests/test_generate_readme.py
git commit -m "Assemble full README rendering with repository meta/badges section"
```

---

### Task 6: `main()` entrypoint and 100% coverage confirmation

**Files:**
- Modify: `scripts/generate_readme.py`
- Modify: `tests/test_generate_readme.py`

**Interfaces:**
- Consumes: `load_resume`, `render_readme` from earlier tasks.
- Produces: `main(repo_root: Path | None = None) -> None` — resolves `repo_root` (defaults to the script's parent's parent directory when not given), loads `repo_root / "resume.yaml"`, writes `repo_root / "README.md"`.
- Consumed by: Task 7 (running the script for real), `hooks/pre-commit` in Task 8 (invokes it as `uv run scripts/generate_readme.py`).

- [ ] **Step 1: Write the failing tests**

Update the import in `tests/test_generate_readme.py` to add `main`. Append:

```python
def test_main_writes_readme_from_resume(tmp_path: Path) -> None:
    (tmp_path / "resume.yaml").write_text(yaml.safe_dump(FULL_RESUME))
    main(repo_root=tmp_path)
    readme = (tmp_path / "README.md").read_text()
    assert "Rah McRae" in readme
    assert TODO not in readme


def test_main_missing_resume_raises_and_writes_nothing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        main(repo_root=tmp_path)
    assert not (tmp_path / "README.md").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_readme.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'main'`.

- [ ] **Step 3: Write the minimal implementation**

Append to `scripts/generate_readme.py`:

```python
def main(repo_root: Path | None = None) -> None:
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    resume = load_resume(repo_root / "resume.yaml")
    (repo_root / "README.md").write_text(render_readme(resume))


if __name__ == "__main__":  # pragma: no cover
    main()
```

- [ ] **Step 4: Run full suite with the coverage gate and verify 100%**

Run: `uv run pytest -v`
Expected: 19 passed, coverage report shows `scripts/generate_readme.py` at 100%, no `FAIL Required test coverage`. If any line shows as missing in the `term-missing` report, add a test covering it before moving on — do not lower `--cov-fail-under` or add unjustified `# pragma: no cover` markers.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_readme.py tests/test_generate_readme.py
git commit -m "Add main() entrypoint, confirm 100% test coverage"
```

---

### Task 7: Generate the real README.md

**Files:**
- Modify: `README.md` (fully replaced — generated content)

**Interfaces:**
- Consumes: `scripts/generate_readme.py` `main()` from Task 6, current (placeholder) `resume.yaml` from Task 1.

- [ ] **Step 1: Run the generator against the real repo**

Run: `uv run scripts/generate_readme.py`
Expected: exits 0, `README.md` is overwritten.

- [ ] **Step 2: Verify the output**

Run: `cat README.md`
Expected: a markdown resume with every section present; since `resume.yaml` is still all placeholders, most fields show `_TODO_` — that's correct and expected at this point (mirrors the old `CONTENT-NEEDED.md` checklist, now expressed as `resume.yaml` gaps).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Replace README.md with resume content generated from resume.yaml"
```

---

### Task 8: Pre-commit hook

**Files:**
- Create: `hooks/pre-commit`

**Interfaces:**
- Consumes: `uv run scripts/generate_readme.py` (Task 6).
- Produces: a hook that regenerates and stages `README.md` whenever `resume.yaml` is part of a commit.

- [ ] **Step 1: Write the hook**

Create `hooks/pre-commit`:

```sh
#!/bin/sh
# Regenerate README.md from resume.yaml whenever resume.yaml is being committed.
set -e

if git diff --cached --name-only | grep -q '^resume\.yaml$'; then
    uv run scripts/generate_readme.py
    git add README.md
fi
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x hooks/pre-commit`

- [ ] **Step 3: Point git at the versioned hooks directory**

Run: `git config core.hooksPath hooks`
Expected: no output; `git config --get core.hooksPath` now prints `hooks`.

- [ ] **Step 4: Manually verify the happy path**

Run:
```bash
sed -i.bak 's/^name: ""/name: "Test Name"/' resume.yaml && rm resume.yaml.bak
git add resume.yaml
git commit -m "test: verify pre-commit hydration"
```
Expected: the commit succeeds, and `git show --stat HEAD` lists both `resume.yaml` and `README.md` as changed. Run `git show HEAD:README.md | grep "Test Name"` to confirm the regenerated content made it into the commit.

- [ ] **Step 5: Manually verify the abort path, then revert the test commit**

Run:
```bash
sed -i.bak 's/name: "Test Name"/name: [unterminated/' resume.yaml && rm resume.yaml.bak
git add resume.yaml
git commit -m "test: verify hook aborts on malformed yaml" || echo "commit correctly blocked"
```
Expected: commit is aborted with the YAML parse error printed. Then clean up:
```bash
git checkout -- resume.yaml
git reset --hard HEAD~1
```
Expected: working tree is back to the state after Task 7's commit (`resume.yaml` back to all-placeholder, no test commits left in history). Run `git status` and `git log --oneline -3` to confirm before moving on.

- [ ] **Step 6: Commit the hook itself**

```bash
git add hooks/pre-commit
git commit -m "Add pre-commit hook to hydrate README.md from resume.yaml"
```

---

### Task 9: GitHub Actions CI — tests, Codecov, Snyk

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `uv run pytest --cov` (Task 6), `pyproject.toml`/`uv.lock` (Task 1).

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3

      - run: uv sync

      - run: uv run pytest --cov-report=xml --cov-report=term-missing

      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

      - uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --file=pyproject.toml
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI: pytest with coverage gate, Codecov upload, Snyk scan"
```

- [ ] **Step 3: Push and confirm the workflow runs**

Run: `git push`
Then: `gh run watch` (or check the Actions tab)
Expected: the `test` job runs `pytest` and uploads to Codecov successfully. The Snyk step will fail until the manual setup in the note below is done — that failure is expected at this point, not a bug in this task.

> **Manual step for the user (not automatable):** connect `rahmcrae/consult-rah-site` at snyk.io and add the token as a repository secret named `SNYK_TOKEN` (Settings → Secrets and variables → Actions). Once added, re-run the workflow and confirm the Snyk step passes.

---

### Task 10: Docs cleanup — remove CONTENT-NEEDED.md, update CLAUDE.md

**Files:**
- Delete: `CONTENT-NEEDED.md`
- Modify: `CLAUDE.md`

**Interfaces:** None — this task only touches documentation.

- [ ] **Step 1: Delete the superseded checklist**

Run: `git rm CONTENT-NEEDED.md`

- [ ] **Step 2: Rewrite `CLAUDE.md`**

Replace the full contents of `CLAUDE.md` with:

```markdown
# consult-rah-site

Personal/consulting static site at consult-rah.com. Defers to the root `.claude/CLAUDE.md` at `_repos/` for process and shared rules.

**Stack:** Single self-contained `index.html` — no framework, no build step, no npm install. Hosted on GitHub Pages with a custom domain (see `CNAME`, `DEPLOYMENT.md`).

**Local preview:** `python3 -m http.server 8000` from this folder, then open `localhost:8000`. Editing `index.html` and refreshing is the whole workflow.

**README.md is generated, not hand-edited.** It's a resume/CV rendered from `resume.yaml` by `scripts/generate_readme.py` (Python, managed via `uv`). To make changes: edit `resume.yaml`, then either run `uv run scripts/generate_readme.py` yourself or just commit — a pre-commit hook regenerates and stages `README.md` automatically whenever `resume.yaml` is part of the commit.

**One-time dev setup:** `uv sync` (installs the Python env), then `git config core.hooksPath hooks` (points git at this repo's versioned pre-commit hook).

**`index.html` and `resume.yaml` are not linked.** `index.html` stays hand-edited; if you update one, check whether the other needs the same update — there's no automation keeping them in sync.

**Files:**

| File | Purpose |
|---|---|
| `index.html` | The entire live site |
| `resume.yaml` | Source of truth for `README.md` content — edit this, not `README.md` |
| `scripts/generate_readme.py` | Renders `resume.yaml` into `README.md` |
| `hooks/pre-commit` | Regenerates `README.md` on commit when `resume.yaml` changes |
| `CNAME` | Tells GitHub Pages to serve this repo at consult-rah.com |
| `robots.txt` | Crawler rules |
| `sitemap.xml` | Single-URL sitemap |
| `DEPLOYMENT.md` | Step-by-step: create the GitHub repo, enable Pages, point DNS |

**CI:** GitHub Actions runs `pytest` with a 100%-coverage gate, uploads coverage to Codecov, and scans dependencies with Snyk on every push/PR.

**Status:** `index.html` structural scaffold is done but still has several `[bracketed, italic]` placeholder sections. `README.md`'s placeholders now live in `resume.yaml` — empty fields there render as `_TODO_` in the generated README.

**Relevant root skills:** `git-workflow`, `python-best-practices` (for `scripts/generate_readme.py` and its tests).
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "Update CLAUDE.md for generated README workflow, drop superseded CONTENT-NEEDED.md"
```
