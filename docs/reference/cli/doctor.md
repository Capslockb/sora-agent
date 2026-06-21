# sora doctor

Run system health checks and report configuration or dependency issues.

## Status

**WORKING** for diagnostics.  
**PLANNED** for auto-fix (`sora doctor --fix`).

## Usage

```bash
sora doctor            # Run all checks
sora doctor --json     # JSON output for CI
sora doctor --fix      # Planned: apply safe fixes automatically
```

## What it checks

- Python version and required packages.
- `~/.sora/config.yaml` and `~/.sora/.env` existence.
- Required API keys presence (Gemini, Discord).
- Optional provider key presence (Vapi, ElevenLabs, OpenAI, xAI, Ultravox, Retell).
- Hermes `discord-voice` plugin availability (for live audio).
- MCP server path and transport.
- VOIP configuration completeness.
- FastAPI dashboard health.

## Verification

```bash
sora doctor
sora doctor --json
```

## Notes

- `--fix` is a stub in the current release. Follow the printed recommendations manually.
- Use `--json` to feed results into CI dashboards.
