from pathlib import Path

import pytest
import yaml

from scripts.generate_readme import (
    TODO,
    load_resume,
    main,
    render_bullet_section,
    render_contact,
    render_experience,
    render_header,
    render_languages,
    render_meta,
    render_projects,
    render_readme,
    render_summary,
)


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


FULL_RESUME = {
    "name": "Rah McRae",
    "title": "Analytics Engineer",
    "location": "Remote",
    "summary": "Builds data platforms and full-stack tools.",
    "contact": {"linkedin": "https://linkedin.com/in/example", "email": "rah@example.com"},
}

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
        "at_a_glance": ["8 years analytics engineering", "Led 3 platform migrations"],
        "core_expertise": ["SQL", "Python", "dbt"],
        "education": ["B.S. Computer Science, Somewhere State"],
        "tech_stack": ["Python", "TypeScript", "AWS"],
    }
)

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
