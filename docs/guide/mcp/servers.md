# MCP Servers

MCP (Model Context Protocol) can connect an agent to external tool servers. In this repository, distinguish three separate surfaces:

1. the static package catalog printed by `sora mcp list` and `sora mcp catalog`;
2. command records saved under `mcp.servers`;
3. the built-in S0RA MCP server, whose only implemented transport is stdio.

None of these surfaces proves that a package is installed, compatible, running, authenticated, or safe for the requested filesystem, network, or account access.

## Built-in catalog

The current CLI catalog names filesystem, GitHub, SQLite, PostgreSQL, fetch, Brave Search, memory, time, and the MCP test server. It is informational package metadata, not an installation or health result.

```bash
sora mcp catalog
```

## Save a command record

```bash
sora mcp add filesystem \
  --command npx \
  --args -y @modelcontextprotocol/server-filesystem /absolute/allowed/path
```

Then inspect or toggle saved state:

```bash
sora mcp status
sora mcp disable filesystem
sora mcp enable filesystem
sora mcp remove filesystem
```

Use the narrowest possible filesystem path and account permissions. Do not place tokens directly in reusable command arguments, screenshots, issue comments, or shared logs.

The saved `enabled` flag is configuration state only. S0RA does not currently supervise each saved command as a managed background service from this command family.

## Built-in S0RA server

```bash
sora mcp start --transport stdio
```

SSE and streamable HTTP are accepted as CLI choices but are not implemented. The custom WebSocket path is incomplete and unsafe to expose. See [MCP Transport Status](websocket.md) and [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).

## Detection boundary

`sora mcp status` and the setup wizard use listener/process heuristics. A matching port or process name is not proof that the process is an MCP server, that it matches the assigned catalog name, or that a usable command record can be reconstructed. Treat detected entries as leads for manual verification only.