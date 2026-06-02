import json

from click.testing import CliRunner

from cli_anything.voicebox.core.session import SessionState, UndoAction
from cli_anything.voicebox.voicebox_cli import main
from cli_anything.voicebox.utils.voicebox_backend import VoiceboxBackend


class FakeBackend:
    profiles = [
        {
            "id": "profile-1",
            "name": "Demo",
            "description": "demo voice",
            "language": "en",
            "voice_type": "preset",
            "preset_engine": "kokoro",
            "preset_voice_id": "af_heart",
            "default_engine": "kokoro",
            "sample_count": 0,
            "generation_count": 0,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        }
    ]
    calls = []

    def __init__(self, base_url="http://fake", timeout=30.0):
        self.base_url = base_url
        self.timeout = timeout

    def get(self, path, *, query=None):
        self.calls.append(("GET", path, query))
        if path == "/profiles":
            return self.profiles
        if path == "/profiles/profile-1":
            return self.profiles[0]
        if path == "/settings/generation":
            return {
                "max_chunk_chars": 800,
                "crossfade_ms": 50,
                "normalize_audio": True,
                "autoplay_on_generate": True,
            }
        return {"path": path, "query": query}

    def post(self, path, *, json_body=None):
        self.calls.append(("POST", path, json_body))
        if path == "/profiles":
            return {**json_body, "id": "profile-2"}
        return {"path": path, "json": json_body}

    def put(self, path, *, json_body=None):
        self.calls.append(("PUT", path, json_body))
        return {"path": path, **(json_body or {})}

    def delete(self, path):
        self.calls.append(("DELETE", path, None))
        return {"deleted": path}


def test_session_round_trip(tmp_path):
    path = tmp_path / "session.json"
    state = SessionState(base_url="http://fake", current_profile_id="profile-1")
    state.push_undo(UndoAction("delete profile", "DELETE", "/profiles/profile-1"))
    state.save(path)

    loaded = SessionState.load(path)

    assert loaded.base_url == "http://fake"
    assert loaded.current_profile_id == "profile-1"
    assert loaded.undo_stack[0].path == "/profiles/profile-1"


def test_profile_list_json(monkeypatch, tmp_path):
    monkeypatch.setenv("VOICEBOX_HARNESS_STATE", str(tmp_path / "state.json"))
    monkeypatch.setattr("cli_anything.voicebox.voicebox_cli.VoiceboxBackend", FakeBackend)

    result = CliRunner().invoke(main, ["--json", "profile", "list"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["id"] == "profile-1"
    assert data[0]["name"] == "Demo"


def test_settings_set_records_undo(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    monkeypatch.setenv("VOICEBOX_HARNESS_STATE", str(state_path))
    monkeypatch.setattr("cli_anything.voicebox.voicebox_cli.VoiceboxBackend", FakeBackend)

    result = CliRunner().invoke(main, ["settings", "set", "generation", "--value", "crossfade_ms=25"])

    assert result.exit_code == 0
    state = SessionState.load(state_path)
    assert state.undo_stack[-1].path == "/settings/generation"
    assert state.undo_stack[-1].json_body == {"crossfade_ms": 50}


def test_backend_builds_query_url():
    backend = VoiceboxBackend("http://example.test")

    assert backend._url("/history", {"limit": 10, "search": None}) == "http://example.test/history?limit=10"
