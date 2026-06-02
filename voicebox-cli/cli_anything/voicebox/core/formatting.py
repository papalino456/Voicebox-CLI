"""Output helpers for the Voicebox CLI harness."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

import click


def _json_default(value: Any) -> str:
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)


def emit(data: Any, *, as_json: bool = False) -> None:
    """Print structured data as JSON or compact human-readable text."""
    if as_json:
        click.echo(json.dumps(data, indent=2, sort_keys=True, default=_json_default))
        return

    if isinstance(data, Mapping):
        for key, value in data.items():
            if isinstance(value, list | dict):
                click.echo(f"{key}: {json.dumps(value, default=_json_default)}")
            else:
                click.echo(f"{key}: {value}")
        return

    if isinstance(data, Iterable) and not isinstance(data, str | bytes):
        for item in data:
            if isinstance(item, Mapping):
                pieces = [f"{key}={value}" for key, value in item.items() if value is not None]
                click.echo("  ".join(pieces))
            else:
                click.echo(str(item))
        return

    click.echo(str(data))


def compact_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Return the profile fields most useful in terminal output."""
    return {
        "id": profile.get("id"),
        "name": profile.get("name"),
        "language": profile.get("language"),
        "voice_type": profile.get("voice_type"),
        "preset_engine": profile.get("preset_engine"),
        "preset_voice_id": profile.get("preset_voice_id"),
        "default_engine": profile.get("default_engine"),
        "sample_count": profile.get("sample_count"),
        "generation_count": profile.get("generation_count"),
    }


def compact_generation(generation: Mapping[str, Any]) -> dict[str, Any]:
    """Return the generation fields most useful in terminal output."""
    text = generation.get("text") or ""
    return {
        "id": generation.get("id"),
        "profile_id": generation.get("profile_id"),
        "profile_name": generation.get("profile_name"),
        "status": generation.get("status"),
        "engine": generation.get("engine"),
        "language": generation.get("language"),
        "text": text[:80],
        "audio_path": generation.get("audio_path"),
        "created_at": generation.get("created_at"),
    }
