# Commands Overview

## Global options

```bash
sora [OPTIONS] <COMMAND> [ARGS]

Options:
  -V, --version          Show version
  --profile NAME         Use named profile
  --tui                  Launch TUI (PLANNED: currently falls back to REPL)
  --cli                  Force CLI mode
  --quiet                Suppress non-error output
  --skin NAME            Override skin (sora, sora-dark, minimal, hermes)
  -h, --help             Show help
```

## Commands overview

| Command | Description | Status |
|---|---|---|
| `chat` | Interactive chat (REPL) | **WORKING** |
| `setup` | Interactive configuration wizard | **WORKING** |
| `voice` | Voice bridge management | **PARTIAL** |
| `mcp` | MCP server management | **PARTIAL** |
| `status` | System status | **WORKING** |
| `cron` | Cron job management | **PLANNED** |
| `doctor` | Health check | **WORKING** (auto-fix **PLANNED**) |
| `logs` | View logs | **PLANNED** |
| `config` | Configuration management | **WORKING** |
| `plugins` | Plugin management | **WORKING** |
| `skills` | Skill management | **PLANNED** |
| `version` | Show version | **WORKING** |
| `update` | Update to latest | **WORKING** |
| `uninstall` | Uninstall S0RA | **WORKING** |
| `acp` | Run as ACP server | **RESEARCH** |
| `tui` | Launch Terminal UI | **PLANNED** |
| `dashboard` | Web dashboard | **WORKING** |
| `providers` | Provider management | **WORKING** |
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
  sip           Manage SIP registration (PARTIAL)
  ari           Manage ARI connection (PARTIAL)
  call          Place outbound call (PARTIAL)
  hangup        Hang up active call(s) (PARTIAL)
  voip-status   Show VOIP bridge status (PARTIAL)
  voip-config   Manage VOIP configuration (PARTIAL)

Providers:
  providers     Manage TTS/STT/LLM Voice providers (WORKING)
```

### MCP subcommands

```bash
sora mcp <SUBCOMMAND>
  start         Start MCP server (PARTIAL: stdio works, HTTP/SSE scaffolded)
  status        Show MCP status (WORKING)
  stop          Stop MCP server (PARTIAL)
  list          List configured servers (WORKING)
  catalog       Browse available servers (WORKING)
  discover      Auto-discover running servers (PARTIAL)
```

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

For full per-command docs see:
- [`sora`](cli/sora.md)
- [`sora setup`](cli/setup.md)
- [`sora doctor`](cli/doctor.md)
- [`sora tui`](cli/tui.md)
- [`sora voice`](cli/voice.md)
- [`sora mcp`](cli/mcp.md)
