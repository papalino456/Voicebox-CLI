"""Persistent session state for the Voicebox CLI harness."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:17493"


def default_state_path() -> Path:
    override = os.environ.get("VOICEBOX_HARNESS_STATE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cli_anything_voicebox" / "session.json"


@dataclass
class UndoAction:
    description: str
    method: str
    path: str
    json_body: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UndoAction":
        return cls(
            description=data["description"],
            method=data["method"],
            path=data["path"],
            json_body=data.get("json_body"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "method": self.method,
            "path": self.path,
            "json_body": self.json_body,
        }


@dataclass
class SessionState:
    base_url: str = DEFAULT_BASE_URL
    current_profile_id: str | None = None
    history: list[str] = field(default_factory=list)
    undo_stack: list[UndoAction] = field(default_factory=list)
    redo_stack: list[UndoAction] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> "SessionState":
        state_path = path or default_state_path()
        if not state_path.exists():
            return cls()

        data = json.loads(state_path.read_text())
        return cls(
            base_url=data.get("base_url", DEFAULT_BASE_URL),
            current_profile_id=data.get("current_profile_id"),
            history=list(data.get("history", [])),
            undo_stack=[UndoAction.from_dict(item) for item in data.get("undo_stack", [])],
            redo_stack=[UndoAction.from_dict(item) for item in data.get("redo_stack", [])],
        )

    def save(self, path: Path | None = None) -> None:
        state_path = path or default_state_path()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "current_profile_id": self.current_profile_id,
            "history": self.history[-200:],
            "undo_stack": [item.to_dict() for item in self.undo_stack[-50:]],
            "redo_stack": [item.to_dict() for item in self.redo_stack[-50:]],
        }

    def remember(self, command: str) -> None:
        if command:
            self.history.append(command)

    def push_undo(self, action: UndoAction) -> None:
        self.undo_stack.append(action)
        self.redo_stack.clear()
