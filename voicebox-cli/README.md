# Voicebox-CLI

Voicebox-CLI is a CLI-Anything harness and Open Agent Skill for operating the local-first [Voicebox](https://github.com/jamiepine/voicebox) backend from agent workflows.

It wraps the real Voicebox REST API. It does not reimplement TTS, model loading, profile storage, or audio generation.

## What This Repo Contains

- `cli-anything-voicebox`: a Python Click CLI for the Voicebox backend
- `skills/voicebox-cli/SKILL.md`: Open Agent Skill instructions for agents
- `scripts/voicebox-cli-agent.js`: npm one-command installer for the CLI and skill
- `scripts/run-cli.js`: npm wrapper for the managed Python CLI
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

## One-Command npm Setup

From this package directory:

```bash
npm run setup
```

After publishing to npm:

```bash
npx voicebox-cli-agent-skill setup
```

This installs:

- the Python CLI into `~/.voicebox-cli/venv`
- the Open Agent Skill into `~/.codex/skills/voicebox-cli`
- a persistent `cli-anything-voicebox` shim into `~/.local/bin`

Then run:

```bash
cli-anything-voicebox --help
npx voicebox-cli-agent-skill status
```

If your shell cannot find `cli-anything-voicebox`, add `~/.local/bin` to `PATH`.

Configuration:

```bash
VOICEBOX_CLI_HOME=/path/to/home npx voicebox-cli-agent-skill setup
VOICEBOX_CLI_BIN_DIR=/path/to/bin npx voicebox-cli-agent-skill setup
VOICEBOX_CLI_PYTHON=python3.12 npx voicebox-cli-agent-skill setup
CODEX_HOME=/path/to/codex-home npx voicebox-cli-agent-skill setup
AGENT_SKILLS_DIR=/path/to/skills npx voicebox-cli-agent-skill setup
```

## Manual CLI Install

```bash
git clone git@github.com:YOUR_USER/Voicebox-CLI.git
cd Voicebox-CLI
cd voicebox-cli
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/cli-anything-voicebox --help
```

If you are using Windows/WSL, keep the Voicebox backend and CLI calls in the same WSL/network context.

## Install The Agent Skill

Install only the skill:

```bash
npm run install-skill
```

Or run the script directly:

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
