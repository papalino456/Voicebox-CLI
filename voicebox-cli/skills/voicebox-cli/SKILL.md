---
name: voicebox-cli
description: Use when an agent needs to install, configure, validate, or operate the Voicebox CLI-Anything harness against a local Voicebox backend, including creating preset voice profiles, generating speech with engines such as Kokoro, checking generated audio files, and handling WSL or localhost backend setup issues.
---

# Voicebox CLI

Use this skill to operate Voicebox through the `cli-anything-voicebox` command instead of driving the desktop UI.

## Source Layout

The Voicebox CLI package contains:

- `setup.py` and `cli_anything/voicebox/`: installable Python CLI package
- `skills/voicebox-cli/`: this Open Agent Skill
- `scripts/install-skill.js`: npm installer that copies the skill into the agent skills directory

## Install The CLI

From the `Voicebox-CLI` repo:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

The command should then be available as:

```bash
.venv/bin/cli-anything-voicebox --help
```

Use the installed path explicitly when working inside agents so shell PATH differences do not hide the command.

## Start Voicebox Backend

Use the real Voicebox backend. Do not reimplement generation.

From a local Voicebox checkout:

```bash
python3 -m venv backend/venv
backend/venv/bin/python -m pip install --upgrade pip
backend/venv/bin/python -m pip install -r backend/requirements.txt
VOICEBOX_MODELS_DIR=/absolute/path/to/voicebox/data/models \
  backend/venv/bin/python -m backend.main --host 127.0.0.1 --port 17493
```

Set `VOICEBOX_MODELS_DIR` to a writable path. In sandboxed or WSL environments, the default Hugging Face cache under `~/.cache/huggingface` may be unavailable.

If localhost calls time out in WSL, start the backend and run the CLI in the same network/security context. For Codex, approved/escalated localhost commands may not see a backend started in a sandboxed session.

## Validate

```bash
cli-anything-voicebox --json health
cli-anything-voicebox --json profile presets kokoro
```

Healthy output should show `status: healthy`, writable data directories, and the expected backend variant.

## Generate With Kokoro

Create a preset profile:

```bash
cli-anything-voicebox --json profile create \
  --name "Kokoro Narrator" \
  --description "Kokoro preset voice" \
  --language en \
  --voice-type preset \
  --preset-engine kokoro \
  --preset-voice-id af_heart \
  --default-engine kokoro
```

Generate speech:

```bash
cli-anything-voicebox --json generate \
  --profile PROFILE_ID \
  --engine kokoro \
  --language en \
  --text "Your script here."
```

Poll completion:

```bash
cli-anything-voicebox --json history get GENERATION_ID
```

The completed record contains `audio_path`, usually `generations/<id>.wav`, relative to the Voicebox data directory.

## Verify Audio

Use Python `soundfile` from the backend venv when available:

```bash
backend/venv/bin/python - <<'PY'
import soundfile as sf
info = sf.info("data/generations/GENERATION_ID.wav")
print(info)
PY
```

Report the absolute file path, duration, sample rate, channel count, engine, voice preset, and generation id.

## CLI Reference

Read `references/cli-commands.md` when you need the command groups and common options.

