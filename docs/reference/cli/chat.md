# sora chat

Interactive chat session with the configured model.

```bash
sora chat [OPTIONS]

Options:
  --model MODEL       Override model (e.g., anthropic/claude-3.5-sonnet)
  --temperature FLOAT Override temperature (0.0-2.0)
  --system PROMPT     Set system prompt
  --no-history        Start fresh (no memory)
```

## In-Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/model <name>` | Switch model |
| `/temp <value>` | Set temperature |
| `/voice <provider>` | Switch voice provider |
| `/providers` | Manage providers |
| `/mcp` | MCP tools |
| `/memory` | Memory commands |
| `/clear` | Clear context |
| `/exit` | Exit chat |
