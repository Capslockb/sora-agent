# CLI Reference

## Global Options

```bash
sora [OPTIONS] <COMMAND> [ARGS]

Options:
  -V, --version          Show version
  --profile NAME         Use named profile
  --tui                  Launch TUI
  --cli                  Force CLI mode
  --quiet                Suppress non-error output
  --skin NAME            Override skin (sora, sora-dark, minimal, hermes)
  -h, --help             Show help
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `chat` | Interactive chat (default) |
| `setup` | Interactive configuration wizard |
| `voice` | Voice bridge management |
| `mcp` | MCP server management |
| `status` | System status |
| `cron` | Cron job management |
| `doctor` | Health check |
| `logs` | View logs |
| `config` | Configuration management |
| `plugins` | Plugin management |
| `skills` | Skill management |
| `version` | Show version |
| `update` | Update to latest |
| `uninstall` | Uninstall S0RA |
| `acp` | Run as ACP server |
| `tui` | Launch Terminal UI |
| `dashboard` | Web dashboard |
| `providers` | Provider management |
| `benchmark` | Performance benchmark |
```

### Voice Subcommands

```bash
sora voice <SUBCOMMAND>

Discord Bridges:
  live          Start Gemini Live bridge
  vapi          Start Vapi bridge
  elevenlabs    Start ElevenLabs bridge
  status        Show voice bridge status
  leave         Stop voice bridge

VOIP (Asterisk + Dograh):
  sip           Manage SIP registration
  ari           Manage ARI connection
  call          Place outbound call
  hangup        Hang up active call(s)
  voip-status   Show VOIP bridge status
  voip-config   Manage VOIP configuration

Providers:
  providers     Manage TTS/STT/LLM Voice providers
```

### MCP Subcommands

```bash
sora mcp <SUBCOMMAND>
  start         Start MCP server
  status        Show MCP status
  stop          Stop MCP server
  list          List configured servers
  catalog       Browse available servers
  discover      Auto-discover running servers
```

### Config Subcommands

```bash
sora config <SUBCOMMAND>
  show          Show current config
  set KEY VAL   Set config value
  get KEY       Get config value
  profiles      List profiles
  profile       Profile management
  reset         Reset to defaults
```

### Plugin Subcommands

```bash
sora plugins <SUBCOMMAND>
  list          List installed plugins
  enable NAME   Enable plugin
  disable NAME  Disable plugin
  install REPO  Install from GitHub
  remove NAME   Remove plugin
  update        Update all plugins
```
