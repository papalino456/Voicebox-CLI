# Voicebox-CLI

Voicebox-CLI is a CLI-Anything harness and Open Agent Skill for operating the local-first [Voicebox](https://github.com/jamiepine/voicebox) backend from agent workflows.

It wraps the real Voicebox REST API. It does not reimplement TTS, model loading, profile storage, or audio generation.

## What This Repo Contains

- `cli-anything-voicebox`: a Python Click CLI for the Voicebox backend
- `skills/voicebox-cli/SKILL.md`: Open Agent Skill instructions for agents
- `scripts/install-skill.js`: npm-style skill installer
- `VOICEBOX.md`: harness design notes
- `TEST.md`: validation plan

## Fork Status

This repo can be pushed as a GitHub fork-style project, but a true GitHub fork must be created on GitHub under your account or organization.

Recommended remote setup:

```bash
git remote add upstream https://github.com/jamiepine/voicebox.git
git remote add origin git@github.com:YOUR_USER/Voicebox-CLI.git
git push -u origin main
```

`upstream` tracks the official Voicebox repo. `origin` should be your GitHub fork or derivative repo named `Voicebox-CLI`.

## Install The CLI

```bash
git clone git@github.com:YOUR_USER/Voicebox-CLI.git
cd Voicebox-CLI
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/cli-anything-voicebox --help
```

If you are using Windows/WSL, keep the Voicebox backend and CLI calls in the same WSL/network context.

## Install The Agent Skill

From this repo:

```bash
npm install
npm run install-skill
```

Or run it without installing dependencies:

```bash
node ./scripts/install-skill.js
```

By default the installer copies `skills/voicebox-cli` to:

```text
~/.codex/skills/voicebox-cli
```

Override locations:

```bash
CODEX_HOME=/path/to/codex-home node ./scripts/install-skill.js
AGENT_SKILLS_DIR=/path/to/skills node ./scripts/install-skill.js
```

## Set Up Voicebox Backend

From a checkout of the official Voicebox app:

```bash
python3 -m venv backend/venv
backend/venv/bin/python -m pip install --upgrade pip
backend/venv/bin/python -m pip install -r backend/requirements.txt
```

Start the backend with a writable model cache:

```bash
VOICEBOX_MODELS_DIR=/absolute/path/to/voicebox/data/models \
  backend/venv/bin/python -m backend.main --host 127.0.0.1 --port 17493
```

Validate with the CLI:

```bash
.venv/bin/cli-anything-voicebox --json health
.venv/bin/cli-anything-voicebox --json profile presets kokoro
```

## Generate Kokoro Speech

Create a Kokoro preset profile:

```bash
.venv/bin/cli-anything-voicebox --json profile create \
  --name "Kokoro Narrator" \
  --description "Kokoro preset voice" \
  --language en \
  --voice-type preset \
  --preset-engine kokoro \
  --preset-voice-id af_heart \
  --default-engine kokoro
```

Generate audio:

```bash
.venv/bin/cli-anything-voicebox --json generate \
  --profile PROFILE_ID \
  --engine kokoro \
  --language en \
  --text "Gravity is the force that pulls objects with mass toward one another."
```

Poll the result:

```bash
.venv/bin/cli-anything-voicebox --json history get GENERATION_ID
```

The `audio_path` field is relative to the Voicebox data directory.

## Development

Run tests:

```bash
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest cli_anything/voicebox/tests
```

Check package install:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/cli-anything-voicebox --json status
```

