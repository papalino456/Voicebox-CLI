"""Stateful Click CLI for operating Voicebox through its real backend."""

from __future__ import annotations

import shlex
from typing import Any

import click

from .core.formatting import compact_generation, compact_profile, emit
from .core.session import DEFAULT_BASE_URL, SessionState, UndoAction
from .utils.voicebox_backend import VoiceboxBackend, VoiceboxBackendError


PASS_CONTEXT = click.make_pass_decorator(dict, ensure=True)


def _backend(ctx: dict[str, Any]) -> VoiceboxBackend:
    return VoiceboxBackend(ctx["state"].base_url, timeout=ctx["timeout"])


def _emit(ctx: dict[str, Any], data: Any) -> None:
    emit(data, as_json=ctx["json"])


def _fail(message: str) -> None:
    raise click.ClickException(message)


def _profile_payload(
    *,
    name: str,
    description: str | None,
    language: str,
    voice_type: str,
    preset_engine: str | None,
    preset_voice_id: str | None,
    design_prompt: str | None,
    default_engine: str | None,
    personality: str | None,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "description": description,
        "language": language,
        "voice_type": voice_type,
        "preset_engine": preset_engine,
        "preset_voice_id": preset_voice_id,
        "design_prompt": design_prompt,
        "default_engine": default_engine,
        "personality": personality,
    }
    return {key: value for key, value in payload.items() if value is not None}


def _profile_to_create_payload(profile: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "name",
        "description",
        "language",
        "voice_type",
        "preset_engine",
        "preset_voice_id",
        "design_prompt",
        "default_engine",
        "personality",
    ]
    return {key: profile.get(key) for key in keys if profile.get(key) is not None}


@click.group(invoke_without_command=True)
@click.option("--base-url", default=None, help=f"Voicebox API URL. Default: {DEFAULT_BASE_URL}")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
@click.option("--timeout", default=30.0, show_default=True, type=float, help="HTTP timeout in seconds.")
@click.pass_context
def main(ctx: click.Context, base_url: str | None, as_json: bool, timeout: float) -> None:
    """CLI-Anything harness for Voicebox."""
    state = SessionState.load()
    if base_url:
        state.base_url = base_url.rstrip("/")
        state.save()

    ctx.obj = {"state": state, "json": as_json, "timeout": timeout}

    if ctx.invoked_subcommand is None:
        repl(ctx)


def repl(ctx: click.Context) -> None:
    """Default interactive mode."""
    click.echo("Voicebox harness REPL. Type 'help' for commands, 'quit' to exit.")
    while True:
        try:
            line = click.prompt("voicebox", default="", show_default=False)
        except (EOFError, KeyboardInterrupt):
            click.echo()
            return

        line = line.strip()
        if not line:
            continue
        if line in {"quit", "exit"}:
            return
        if line == "help":
            click.echo(ctx.get_help())
            continue

        state: SessionState = ctx.obj["state"]
        state.remember(line)
        state.save()
        try:
            main.main(args=shlex.split(line), prog_name="cli-anything-voicebox", standalone_mode=False, obj=ctx.obj)
        except click.ClickException as exc:
            exc.show()
        except SystemExit:
            pass


@main.command()
@PASS_CONTEXT
def status(ctx: dict[str, Any]) -> None:
    """Show harness session status."""
    state: SessionState = ctx["state"]
    _emit(
        ctx,
        {
            "base_url": state.base_url,
            "current_profile_id": state.current_profile_id,
            "undo_depth": len(state.undo_stack),
            "redo_depth": len(state.redo_stack),
        },
    )


@main.command()
@PASS_CONTEXT
def health(ctx: dict[str, Any]) -> None:
    """Check backend and filesystem health."""
    try:
        backend = _backend(ctx)
        result = {
            "root": backend.get("/"),
            "health": backend.get("/health"),
            "filesystem": backend.get("/health/filesystem"),
        }
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@main.command("undo")
@PASS_CONTEXT
def undo_command(ctx: dict[str, Any]) -> None:
    """Run the latest reversible inverse operation."""
    state: SessionState = ctx["state"]
    if not state.undo_stack:
        _fail("Nothing to undo.")

    action = state.undo_stack.pop()
    try:
        result = _backend(ctx).request(action.method, action.path, json_body=action.json_body)
    except VoiceboxBackendError as exc:
        state.undo_stack.append(action)
        state.save()
        _fail(str(exc))

    state.redo_stack.append(action)
    state.save()
    _emit(ctx, {"undone": action.description, "result": result})


@main.command("redo")
@PASS_CONTEXT
def redo_command(ctx: dict[str, Any]) -> None:
    """Re-run the latest inverse operation."""
    state: SessionState = ctx["state"]
    if not state.redo_stack:
        _fail("Nothing to redo.")

    action = state.redo_stack.pop()
    try:
        result = _backend(ctx).request(action.method, action.path, json_body=action.json_body)
    except VoiceboxBackendError as exc:
        state.redo_stack.append(action)
        state.save()
        _fail(str(exc))

    state.undo_stack.append(action)
    state.save()
    _emit(ctx, {"redone": action.description, "result": result})


@main.group()
def profile() -> None:
    """Manage voice profiles."""


@profile.command("list")
@PASS_CONTEXT
def profile_list(ctx: dict[str, Any]) -> None:
    """List voice profiles."""
    try:
        profiles = _backend(ctx).get("/profiles")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, [compact_profile(item) for item in profiles])


@profile.command("get")
@click.argument("profile_id", required=False)
@PASS_CONTEXT
def profile_get(ctx: dict[str, Any], profile_id: str | None) -> None:
    """Show one profile."""
    state: SessionState = ctx["state"]
    profile_id = profile_id or state.current_profile_id
    if not profile_id:
        _fail("Provide PROFILE_ID or select one with profile use.")
    try:
        result = _backend(ctx).get(f"/profiles/{profile_id}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@profile.command("use")
@click.argument("profile_id")
@PASS_CONTEXT
def profile_use(ctx: dict[str, Any], profile_id: str) -> None:
    """Select the current profile for generation commands."""
    try:
        _backend(ctx).get(f"/profiles/{profile_id}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    state: SessionState = ctx["state"]
    state.current_profile_id = profile_id
    state.save()
    _emit(ctx, {"current_profile_id": profile_id})


@profile.command("create")
@click.option("--name", required=True, help="Profile name.")
@click.option("--description", default=None, help="Profile description.")
@click.option("--language", default="en", show_default=True, help="Voice language code.")
@click.option("--voice-type", default="cloned", show_default=True, type=click.Choice(["cloned", "preset", "designed"]))
@click.option("--preset-engine", default=None, help="Preset engine, for preset profiles.")
@click.option("--preset-voice-id", default=None, help="Preset voice id, for preset profiles.")
@click.option("--design-prompt", default=None, help="Voice design prompt, for designed profiles.")
@click.option("--default-engine", default=None, help="Default generation engine for this profile.")
@click.option("--personality", default=None, help="Optional personality prompt.")
@PASS_CONTEXT
def profile_create(ctx: dict[str, Any], **kwargs: Any) -> None:
    """Create a voice profile."""
    payload = _profile_payload(**kwargs)
    try:
        result = _backend(ctx).post("/profiles", json_body=payload)
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    state: SessionState = ctx["state"]
    state.current_profile_id = result.get("id")
    state.push_undo(UndoAction(f"delete profile {result.get('id')}", "DELETE", f"/profiles/{result.get('id')}"))
    state.save()
    _emit(ctx, result)


@profile.command("update")
@click.argument("profile_id", required=False)
@click.option("--name", default=None, help="Profile name.")
@click.option("--description", default=None, help="Profile description.")
@click.option("--language", default=None, help="Voice language code.")
@click.option("--voice-type", default=None, type=click.Choice(["cloned", "preset", "designed"]))
@click.option("--preset-engine", default=None, help="Preset engine.")
@click.option("--preset-voice-id", default=None, help="Preset voice id.")
@click.option("--design-prompt", default=None, help="Voice design prompt.")
@click.option("--default-engine", default=None, help="Default generation engine.")
@click.option("--personality", default=None, help="Personality prompt.")
@PASS_CONTEXT
def profile_update(ctx: dict[str, Any], profile_id: str | None, **kwargs: Any) -> None:
    """Update a voice profile."""
    state: SessionState = ctx["state"]
    profile_id = profile_id or state.current_profile_id
    if not profile_id:
        _fail("Provide PROFILE_ID or select one with profile use.")

    try:
        backend = _backend(ctx)
        previous = backend.get(f"/profiles/{profile_id}")
        payload = _profile_to_create_payload(previous)
        payload.update({key: value for key, value in kwargs.items() if value is not None})
        result = backend.put(f"/profiles/{profile_id}", json_body=payload)
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    state.push_undo(
        UndoAction(
            f"restore profile {profile_id}",
            "PUT",
            f"/profiles/{profile_id}",
            _profile_to_create_payload(previous),
        )
    )
    state.save()
    _emit(ctx, result)


@profile.command("delete")
@click.argument("profile_id", required=False)
@PASS_CONTEXT
def profile_delete(ctx: dict[str, Any], profile_id: str | None) -> None:
    """Delete a voice profile."""
    state: SessionState = ctx["state"]
    profile_id = profile_id or state.current_profile_id
    if not profile_id:
        _fail("Provide PROFILE_ID or select one with profile use.")

    try:
        backend = _backend(ctx)
        previous = backend.get(f"/profiles/{profile_id}")
        result = backend.delete(f"/profiles/{profile_id}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    if state.current_profile_id == profile_id:
        state.current_profile_id = None
    state.push_undo(UndoAction(f"recreate profile {profile_id}", "POST", "/profiles", _profile_to_create_payload(previous)))
    state.save()
    _emit(ctx, result)


@profile.command("presets")
@click.argument("engine", type=click.Choice(["kokoro", "qwen_custom_voice"]))
@PASS_CONTEXT
def profile_presets(ctx: dict[str, Any], engine: str) -> None:
    """List preset voices for an engine."""
    try:
        result = _backend(ctx).get(f"/profiles/presets/{engine}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@profile.command("sample-add")
@click.argument("profile_id")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--reference-text", required=True)
@PASS_CONTEXT
def profile_sample_add(ctx: dict[str, Any], profile_id: str, file_path: str, reference_text: str) -> None:
    """Upload a voice sample to a profile."""
    try:
        result = _backend(ctx).upload_file(
            f"/profiles/{profile_id}/samples",
            file_path=file_path,
            fields={"reference_text": reference_text},
        )
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@main.command()
@click.option("--profile", "profile_id", default=None, help="Profile id. Defaults to current profile.")
@click.option("--text", required=True, help="Text to generate.")
@click.option("--language", default="en", show_default=True)
@click.option("--engine", default="qwen", show_default=True)
@click.option("--seed", default=None, type=int)
@click.option("--model-size", default="1.7B", show_default=True)
@click.option("--instruct", default=None)
@click.option("--personality", is_flag=True)
@click.option("--max-chunk-chars", default=800, show_default=True, type=int)
@click.option("--crossfade-ms", default=50, show_default=True, type=int)
@click.option("--normalize/--no-normalize", default=True, show_default=True)
@PASS_CONTEXT
def generate(ctx: dict[str, Any], profile_id: str | None, **kwargs: Any) -> None:
    """Submit a speech generation job."""
    state: SessionState = ctx["state"]
    profile_id = profile_id or state.current_profile_id
    if not profile_id:
        _fail("Provide --profile or select one with profile use.")

    payload = {"profile_id": profile_id, **{key: value for key, value in kwargs.items() if value is not None}}
    try:
        result = _backend(ctx).post("/generate", json_body=payload)
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@main.group()
def history() -> None:
    """Inspect generation history."""


@history.command("list")
@click.option("--profile", "profile_id", default=None)
@click.option("--search", default=None)
@click.option("--limit", default=20, show_default=True, type=int)
@click.option("--offset", default=0, show_default=True, type=int)
@PASS_CONTEXT
def history_list(ctx: dict[str, Any], profile_id: str | None, search: str | None, limit: int, offset: int) -> None:
    """List generation history."""
    try:
        result = _backend(ctx).get(
            "/history",
            query={"profile_id": profile_id, "search": search, "limit": limit, "offset": offset},
        )
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    output = {
        "total": result.get("total", 0),
        "items": [compact_generation(item) for item in result.get("items", [])],
    }
    _emit(ctx, output)


@history.command("get")
@click.argument("generation_id")
@PASS_CONTEXT
def history_get(ctx: dict[str, Any], generation_id: str) -> None:
    """Show a generation history item."""
    try:
        result = _backend(ctx).get(f"/history/{generation_id}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@history.command("stats")
@PASS_CONTEXT
def history_stats(ctx: dict[str, Any]) -> None:
    """Show generation statistics."""
    try:
        result = _backend(ctx).get("/history/stats")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@history.command("favorite")
@click.argument("generation_id")
@PASS_CONTEXT
def history_favorite(ctx: dict[str, Any], generation_id: str) -> None:
    """Toggle favorite state for a generation."""
    try:
        result = _backend(ctx).post(f"/history/{generation_id}/favorite")
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    state: SessionState = ctx["state"]
    state.push_undo(UndoAction(f"toggle favorite {generation_id}", "POST", f"/history/{generation_id}/favorite"))
    state.save()
    _emit(ctx, result)


@history.command("clear-failed")
@PASS_CONTEXT
def history_clear_failed(ctx: dict[str, Any]) -> None:
    """Delete failed generations."""
    try:
        result = _backend(ctx).delete("/history/failed")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@main.group()
def settings() -> None:
    """Read or update settings."""


@settings.command("get")
@click.argument("domain", type=click.Choice(["captures", "generation"]))
@PASS_CONTEXT
def settings_get(ctx: dict[str, Any], domain: str) -> None:
    """Get capture or generation settings."""
    try:
        result = _backend(ctx).get(f"/settings/{domain}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@settings.command("set")
@click.argument("domain", type=click.Choice(["captures", "generation"]))
@click.option("--value", "values", multiple=True, help="Setting as key=value. Repeat for multiple values.")
@PASS_CONTEXT
def settings_set(ctx: dict[str, Any], domain: str, values: tuple[str, ...]) -> None:
    """Patch capture or generation settings."""
    if not values:
        _fail("Provide at least one --value key=value.")

    patch = dict(_parse_key_value(item) for item in values)
    try:
        backend = _backend(ctx)
        previous = backend.get(f"/settings/{domain}")
        result = backend.put(f"/settings/{domain}", json_body=patch)
    except VoiceboxBackendError as exc:
        _fail(str(exc))

    inverse = {key: previous.get(key) for key in patch}
    state: SessionState = ctx["state"]
    state.push_undo(UndoAction(f"restore {domain} settings", "PUT", f"/settings/{domain}", inverse))
    state.save()
    _emit(ctx, result)


def _parse_key_value(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        _fail(f"Expected key=value, got: {raw}")
    key, value = raw.split("=", 1)
    lowered = value.lower()
    if lowered in {"true", "false"}:
        parsed: Any = lowered == "true"
    else:
        try:
            parsed = int(value)
        except ValueError:
            parsed = value
    return key, parsed


@main.group()
def model() -> None:
    """Inspect and manage models."""


@model.command("cache-dir")
@PASS_CONTEXT
def model_cache_dir(ctx: dict[str, Any]) -> None:
    """Show Hugging Face model cache directory."""
    try:
        result = _backend(ctx).get("/models/cache-dir")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@model.command("status")
@PASS_CONTEXT
def model_status(ctx: dict[str, Any]) -> None:
    """Show model status list."""
    try:
        result = _backend(ctx).get("/models/status")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@model.command("load")
@click.option("--model-size", default="1.7B", show_default=True)
@PASS_CONTEXT
def model_load(ctx: dict[str, Any], model_size: str) -> None:
    """Load the default Qwen TTS model."""
    try:
        result = _backend(ctx).post(f"/models/load?model_size={model_size}")
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@model.command("unload")
@click.argument("model_name", required=False)
@PASS_CONTEXT
def model_unload(ctx: dict[str, Any], model_name: str | None) -> None:
    """Unload the default or named model from memory."""
    path = f"/models/{model_name}/unload" if model_name else "/models/unload"
    try:
        result = _backend(ctx).post(path)
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


@model.command("download")
@click.argument("model_name")
@PASS_CONTEXT
def model_download(ctx: dict[str, Any], model_name: str) -> None:
    """Trigger a model download through the backend."""
    try:
        result = _backend(ctx).post("/models/download", json_body={"model_name": model_name})
    except VoiceboxBackendError as exc:
        _fail(str(exc))
    _emit(ctx, result)


if __name__ == "__main__":
    main()
