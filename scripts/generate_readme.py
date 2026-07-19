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
