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
