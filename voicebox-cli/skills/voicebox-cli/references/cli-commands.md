# Voicebox CLI Commands

The CLI command is `cli-anything-voicebox`.

Global options:

- `--base-url URL`: Voicebox API URL, default `http://127.0.0.1:17493`
- `--json`: machine-readable output
- `--timeout SECONDS`: HTTP timeout

Commands:

- `status`: show harness state
- `health`: call `/`, `/health`, and `/health/filesystem`
- `profile list`: list profiles
- `profile get [PROFILE_ID]`: show a profile
- `profile use PROFILE_ID`: select a current profile
- `profile create ...`: create a profile
- `profile update [PROFILE_ID] ...`: update metadata
- `profile delete [PROFILE_ID]`: delete a profile
- `profile presets kokoro`: list Kokoro preset voices
- `profile sample-add PROFILE_ID --file PATH --reference-text TEXT`: upload cloned-voice sample
- `generate --profile PROFILE_ID --engine ENGINE --language LANG --text TEXT`: submit speech generation
- `history list`: list generations
- `history get GENERATION_ID`: inspect a generation
- `history stats`: generation statistics
- `history favorite GENERATION_ID`: toggle favorite
- `history clear-failed`: remove failed generations
- `settings get captures|generation`: read settings
- `settings set captures|generation --value key=value`: patch settings
- `model cache-dir`: show model cache
- `model status`: list model status
- `model download MODEL_NAME`: trigger download
- `model load --model-size 1.7B`: load default Qwen model
- `model unload [MODEL_NAME]`: unload model
- `undo` / `redo`: run reversible harness actions where supported

Kokoro preset profile payload:

```bash
cli-anything-voicebox --json profile create \
  --name "Kokoro Narrator" \
  --language en \
  --voice-type preset \
  --preset-engine kokoro \
  --preset-voice-id af_heart \
  --default-engine kokoro
```

