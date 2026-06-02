# Test Plan

## Unit Coverage

`cli_anything/voicebox/tests/test_core.py`

- formats JSON and human-readable output deterministically
- persists and reloads session state
- records undo/redo entries
- verifies backend request construction using a fake transport

## Full E2E Coverage

`cli_anything/voicebox/tests/test_full_e2e.py`

- invokes the installed console script with `--help`
- exercises the root command's default REPL path through `quit`
- verifies `--json` output with a fake backend URL where possible

## Manual Backend Validation

With Voicebox running:

```bash
python3 -m backend.main --host 127.0.0.1 --port 17493
cd agent-harness
python3 -m pip install -e .
cli-anything-voicebox health --json
cli-anything-voicebox profile list --json
cli-anything-voicebox settings get generation --json
```

Generation commands may download models or run inference through the real backend. Use them deliberately:

```bash
cli-anything-voicebox generate --profile PROFILE_ID --text "Smoke test" --engine kokoro
```
