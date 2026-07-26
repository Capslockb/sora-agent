# Commands Overview

## Global options

```bash
sora [OPTIONS] <COMMAND> [ARGS]

Options:
  -V, --version          Show version
  --profile NAME         Use named profile
  --tui                  Request TUI mode for interface-aware paths
  --cli                  Force CLI mode
  --quiet                Suppress non-error output
  --skin NAME            Override skin (sora, sora-dark, minimal, hermes)
  -h, --help             Show help
```

The `--tui` flag is not equivalent to the `sora tui` subcommand. The subcommand launches the separately built Ink/React prototype described below; the global flag sets interface selection for code paths that inspect `SORA_TUI` or `display.interface`.

## Commands overview

| Command | Description | Status |
|---|---|---|
| `chat` | Interactive chat (REPL) | **WORKING** |
| `setup` | Interactive configuration wizard; provider setup is incomplete and does not share one canonical state model | **PARTIAL** |
| `voice` | Voice bridge management | **PARTIAL** |
| `mcp` | MCP configuration and experimental server surfaces | **PARTIAL** |
| `status` | System status | **WORKING** |
| `cron` | Cron job management | **PLANNED** |
| `doctor` | Health check | **WORKING** (auto-fix **PLANNED**) |
| `logs` | View logs | **PLANNED** |
| `config` | Configuration management | **WORKING** |
| `plugins` | Plugin management | **WORKING** |
| `skills` | Skill management | **PLANNED** |
| `version` | Show version | **WORKING** |
| `update` | In-place update for a compatible clean Git checkout; not a general pipx upgrade path | **PARTIAL** |
| `uninstall` | Uninstall S0RA | **WORKING** |
| `acp` | Run as ACP server | **RESEARCH** |
| `tui` | Launch the locally built Ink/React prototype; current panels use simulated or hard-coded data | **PARTIAL — PROTOTYPE** |
| `dashboard` | Trusted-local-development dashboard; `--host` constrains the API only, not the separately launched UI preview. See Issue #13. | **PARTIAL** |
| `providers` | Provider configuration through a registry that diverges from `sora voice providers`, setup, and the dashboard/API | **PARTIAL** |
| `benchmark` | Performance benchmark | **WORKING** |

### Voice subcommands

```bash
sora voice <SUBCOMMAND>

Discord Bridges:
  live          Prepare/start Gemini Live bridge (PARTIAL: runtime in Hermes discord-voice)
  vapi          Prepare/start Vapi bridge (PARTIAL)
  elevenlabs    Prepare/start ElevenLabs bridge (PARTIAL)
  status        Show voice bridge status (WORKING)
  leave         Stop voice bridge (PARTIAL)

VOIP (Asterisk + Dograh):
  sip           SIP compatibility/configuration surface (PARTIAL; dynamic registration is not working)
  ari           Manage ARI configuration/status (PARTIAL; active operations require an initialized bridge)
  call          Place outbound call (BLOCKED by Issue #14)
  hangup        Hang up active call(s) (BLOCKED by Issue #14)
  voip-status   Show VOIP bridge status (BLOCKED unless a compatible bridge is already running)
  voip-config   Manage VOIP configuration (PARTIAL; do not pass secrets positionally; see Issue #7)

Providers:
  providers     Manage a nested provider registry (PARTIAL; not equivalent to top-level `sora providers`)
```

The checked-in VOIP startup entrypoints cannot currently construct `VoipBridge`, so command presence is not evidence of a runnable phone bridge. Track the lifecycle repair in [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

The top-level `sora providers`, nested `sora voice providers`, setup wizard, and dashboard/API do not currently share one canonical provider schema or selection contract. Treat their output as surface-specific configuration state, not authoritative provider health. Track unification in [Issue #15](https://github.com/Capslockb/sora-agent/issues/15).

### MCP subcommands

```bash
sora mcp <SUBCOMMAND>
  start             Start the built-in server (PARTIAL: stdio only)
  status            Show saved records plus heuristic listener/process detection (PARTIAL)
  list              Print the built-in package catalog
  catalog           Alias of list
  add                Save a command-based server record
  remove             Remove a saved server record
  enable / disable   Toggle a saved record
  ws start           Start the incomplete unauthenticated WebSocket listener (EXPERIMENTAL)
  ws stop/status/list
                    Parser-visible stubs that return not implemented
```

Top-level `sora mcp stop` and `sora mcp discover` are not registered commands. `sora mcp start --transport sse` and `--transport streamable-http` are accepted by the parser but raise `NotImplementedError`; no `/sse` or `/mcp` HTTP endpoint is created. `status` does not perform an MCP handshake, and `list` shows the static package catalog rather than saved server configuration. Do not expose the custom WebSocket listener or treat listener/process matches as verified MCP health. See [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).

### TUI subcommand

```bash
sora tui
sora tui --build
```

Plain `sora tui` launches `ui-tui/dist/cli.js` only when that bundle exists. It does not fall back to the chat REPL. `--build` currently runs `npm install` and `npx esbuild`; the build path is not yet lockfile-enforced or no-download.

The resulting interface is an unverified prototype. Voice actions are simulated, status/provider values are hard-coded, doctor output is fixed, benchmark values are random, setup/configuration is display-only, and the MCP panel advertises unsupported commands and transports. Do not treat it as a live management, configuration, doctor, benchmark, or health surface. See [Issue #17](https://github.com/Capslockb/sora-agent/issues/17).

### Config subcommands

```bash
sora config <SUBCOMMAND>
  show          Show current config
  set KEY VAL   Set config value
  get KEY       Get config value
  profiles      List profiles
  profile       Profile management
  reset         Reset to defaults
```

### Plugin subcommands

```bash
sora plugins <SUBCOMMAND>
  list          List installed plugins
  enable NAME   Enable plugin
  disable NAME  Disable plugin
  install REPO  Install from GitHub
  remove NAME   Remove plugin
  update        Update all plugins
```

### Update command

```bash
sora update --check-only
sora update
```

The current updater is **not** a general package-manager upgrade command. It only attempts an in-place update when the installed source directory itself contains a Git checkout. It hard-codes `origin/main`, performs `git pull`, and then runs `uv pip install -e` against that checkout.

A normal `pipx install git+https://github.com/Capslockb/sora-agent` installation does not remain a Git checkout at the installed module path, so `sora update` exits without upgrading it. For pipx installations, reinstall from the same repository URL instead:

```bash
pipx install --force git+https://github.com/Capslockb/sora-agent
```

Do not run the in-place updater from a checkout with uncommitted work, a detached HEAD, a divergent branch, or an unverified remote/upstream. These states are not preflighted before mutation. Track the installation-aware lifecycle repair in [Issue #18](https://github.com/Capslockb/sora-agent/issues/18).

For full per-command docs see:
- [`sora`](cli/sora.md)
- [`sora setup`](cli/setup.md)
- [`sora doctor`](cli/doctor.md)
- [`sora tui`](cli/tui.md)
- [`sora voice`](cli/voice.md)
- [`sora mcp`](cli/mcp.md)
