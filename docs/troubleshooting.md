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

### `sora tui` says the TUI is not built

Plain `sora tui` launches `ui-tui/dist/cli.js` only when that local bundle exists. It does not fall back to the chat REPL.

```bash
sora tui --build
```

The current build path runs `npm install` and `npx esbuild`; it is not yet the lockfile-enforced, no-download build required by Issue #7. The resulting Ink/React interface is also a prototype: voice activity is simulated, status/provider values are hard-coded, doctor output is fixed, benchmark values are random, setup is display-only, and the MCP panel contains unsupported commands and transports.

Use the current interface only as an explicitly labeled prototype preview. Do not treat any panel as live operational evidence and do not enter real credentials. Track correction in [Issue #17](https://github.com/Capslockb/sora-agent/issues/17).

### `sora doctor --fix` does nothing

Expected — auto-fix is **PLANNED**. `sora doctor` reports issues; manual fixes are required.

### Dashboard port already in use

The dashboard UI preview and control API use separate ports. Change the occupied port explicitly:

```bash
sora dashboard start --host 127.0.0.1 --port 3001 --api-port 8081
```

`--port` controls the dashboard UI preview port (default `3000`), while `--api-port` controls the API port (default `8080`). Keep them different. `--host` currently controls only the API bind; the UI preview is launched separately through `npx serve` without an explicit host argument.

Until Issue #13 is resolved, use the dashboard only on a trusted local machine. Do not bind the unauthenticated control API to `0.0.0.0`, and do not run or publish either listener on a shared host, LAN interface, tunnel, container-published interface, reverse proxy, or public endpoint.

### MCP server starts but Hermes cannot see it

S0RA MCP currently defaults to **stdio**. For Hermes integration, register it with `hermes mcp add sora-agent` and point to `python -m sora mcp start`.

### VOIP bridge shows `stopped`

The VOIP bridge requires an external Asterisk PBX and Dograh gateway. Set `SORA_ARI_URL`, `SORA_ARI_USER`, `SORA_ARI_PASSWORD`, and `SORA_DOGRAH_WS_URL` in `~/.sora/.env`.

## Still stuck?

1. Run `sora doctor` and read the output.
2. Check `~/.sora/logs/`.
3. Re-run the failing command with `--verbose` if available.
4. Open an issue with the output of `sora --version`, `sora doctor`, and `sora status --json`.