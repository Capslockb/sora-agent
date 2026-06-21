# Troubleshooting

Common issues when installing or running S0RA, plus where to look for logs.

## Where to look

| Path | What |
|---|---|
| `~/.sora/config.yaml` | Active profile configuration |
| `~/.sora/.env` | Secrets |
| `~/.sora/logs/` | S0RA logs |
| `~/.sora/state.db` | SQLite runtime state |
| `tests/` | pytest suite |

## Common issues

### `sora: command not found`

Ensure `pipx` binaries are on your PATH:

```bash
pipx ensurepath
# or, for a local install:
python -m sora --help
```

### `sora setup` says a provider is unavailable

Provider availability depends on the corresponding API key in `~/.sora/.env`. The wizard shows the key as missing before it asks for it.

### `sora voice live` does not connect to Discord

S0RA does not contain the live Discord audio runtime. The command prepares bridge arguments and delegates to the Hermes `discord-voice` plugin. Verify:

```bash
hermes plugins list | grep discord-voice
hermes tools list | grep sora_voice
```

If `discord-voice` is not installed, install and enable it first.

### `sora tui` shows a REPL, not a TUI

Expected — the TUI is **PLANNED**. `sora tui` currently falls back to a chat REPL.

### `sora doctor --fix` does nothing

Expected — auto-fix is **PLANNED**. `sora doctor` reports issues; manual fixes are required.

### Dashboard port already in use

```bash
sora dashboard start --port 8081
# or set SORA_API_PORT=8081
```

### MCP server starts but Hermes cannot see it

S0RA MCP currently defaults to **stdio**. For Hermes integration, register it with `hermes mcp add sora-agent` and point to `python -m sora mcp start`.

### VOIP bridge shows `stopped`

The VOIP bridge requires an external Asterisk PBX and Dograh gateway. Set `SORA_ARI_URL`, `SORA_ARI_USER`, `SORA_ARI_PASSWORD`, and `SORA_DOGRAH_WS_URL` in `~/.sora/.env`.

## Still stuck?

1. Run `sora doctor` and read the output.
2. Check `~/.sora/logs/`.
3. Re-run the failing command with `--verbose` if available.
4. Open an issue with the output of `sora --version`, `sora doctor`, and `sora status --json`.
