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
