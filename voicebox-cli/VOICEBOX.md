# CLI-Anything Harness: Voicebox

Target software: Voicebox, the local-first AI voice studio in `/home/sebastian/voicebox`.

This harness exposes a stateful command line interface over the real Voicebox HTTP API. It is intended for headless inspection, smoke testing, and scripted operation of the backend without driving the Tauri GUI.

## Backend Mapping

- Health: `GET /`, `GET /health`, `GET /health/filesystem`
- Profiles: `GET/POST/PUT/DELETE /profiles`, preset voice listing, sample upload
- Generation: `POST /generate`, status lookup through history and task endpoints
- History: `GET /history`, stats, favorite toggles, failed-generation cleanup
- Settings: `GET/PUT /settings/captures`, `GET/PUT /settings/generation`
- Models: cache directory, status/download/load/unload operations

The harness does not reimplement TTS, STT, profile persistence, or model management. It wraps the running backend at `--base-url`, defaulting to `http://127.0.0.1:17493`.

## State Model

Session state is persisted in `~/.cli_anything_voicebox/session.json` unless `VOICEBOX_HARNESS_STATE` is set. The state stores:

- current API base URL
- current selected profile
- command history
- undo and redo stacks

Undo/redo is supported for reversible profile and settings changes:

- `profile create` can be undone by deleting the created profile
- `profile delete` can be undone by recreating the profile metadata
- `profile update` can restore the previous metadata
- `settings set` can restore previous setting values
- `history favorite` can toggle back

Operations that involve uploaded audio, generated audio, or model downloads are not fully reversible and are not added to the undo stack.

## Installation

```bash
cd /home/sebastian/voicebox/agent-harness
python3 -m pip install -e .
```

## Examples

```bash
cli-anything-voicebox health --json
cli-anything-voicebox profile list
cli-anything-voicebox profile create --name "Demo" --description "Harness profile" --language en
cli-anything-voicebox profile use PROFILE_ID
cli-anything-voicebox generate --text "Hello from the harness" --engine kokoro --json
cli-anything-voicebox history list --limit 10
cli-anything-voicebox settings get generation
cli-anything-voicebox undo
```

Running `cli-anything-voicebox` without a subcommand starts the REPL.
