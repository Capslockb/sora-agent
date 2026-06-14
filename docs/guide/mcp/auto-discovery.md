# MCP Auto-Discovery

S0RA automatically detects running MCP servers on your machine.

## Detection Methods

| Method | Ports/Paths | Examples |
|--------|-------------|----------|
| HTTP Scan | 3000-3010 | MCP servers on localhost |
| Stdio Scan | Process list | `npx @modelcontextprotocol/server-*` |
| Config Files | `~/.mcp.json`, `.mcp.json` | Project-local servers |

## Setup Wizard Integration

During `sora setup`:

```
Scanning for running MCP servers...
✓ Found running MCP servers: filesystem, github
  • filesystem: File operations (port 3001)
  • github: GitHub API (port 3002)
  Add filesystem to Sora config? [Y/n]
  Add github to Sora config? [Y/n]
```

## Manual Trigger

```bash
# Re-scan
sora mcp discover

# Add discovered server
sora mcp add filesystem --port 3001
```
