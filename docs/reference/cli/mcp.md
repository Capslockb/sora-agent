# sora mcp

MCP (Model Context Protocol) server management.

```bash
sora mcp <SUBCOMMAND>
```

## Commands

| Command | Description |
|---------|-------------|
| `start` | Start MCP server (stdio + WebSocket) |
| `status` | Show server status |
| `stop` | Stop MCP server |
| `list` | List configured servers |
| `catalog` | Browse available servers |
| `discover` | Auto-discover running servers |

## Start Options

```bash
sora mcp start [--port 3000] [--transport streamable-http|sse|stdio]
```

## WebSocket MCP

| Transport | Endpoint |
|-----------|----------|
| streamable-http | `http://localhost:3000/mcp` |
| sse | `http://localhost:3000/sse` |
| WebSocket | `ws://localhost:3000/ws` |
