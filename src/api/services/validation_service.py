from __future__ import annotations


def sanitize_text(value: str) -> str:
    return value.replace("<", "&lt;").replace(">", "&gt;").strip()


def validate_non_empty(value: str | None, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
