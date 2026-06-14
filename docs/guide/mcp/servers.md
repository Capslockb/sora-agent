# MCP Servers

MCP (Model Context Protocol) lets S0RA connect to external tools and data sources.

## Supported Servers

| Server | Transport | Description |
|--------|-----------|-------------|
| Filesystem | stdio | Local file operations |
| GitHub | HTTP | Repos, issues, PRs |
| PostgreSQL | stdio | Database queries |
| SQLite | stdio | Local database |
| Browser | stdio | Puppeteer automation |
| Git | stdio | Git operations |
| Custom | stdio/HTTP | Your own servers |

## Configuration

```yaml
mcp:
  enabled: true
  servers:
    filesystem:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    github:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
```

## CLI

```bash
# Start MCP server (stdio + WebSocket)
sora mcp start --port 3000 --transport streamable-http

# Status
sora mcp status

# List configured servers
sora mcp list

# Catalog available servers
sora mcp catalog
```
