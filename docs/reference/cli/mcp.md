# sora mcp

Manage S0RA's MCP configuration and the built-in experimental server surfaces.

```bash
sora mcp <SUBCOMMAND>
```

## Registered commands

| Command | Current behavior |
|---|---|
| `start` | Run the built-in server. Only `--transport stdio` is implemented. |
| `status` | Print saved server records and heuristic process/listener detection. It does not verify MCP protocol health. |
| `list` | Print the built-in package catalog. It does not list saved configuration. |
| `catalog` | Alias of `list`. |
| `add` | Save a command-based server record. |
| `remove` | Remove a saved server record. |
| `enable` / `disable` | Toggle the saved record's `enabled` flag. |
| `ws start` | Start the incomplete custom WebSocket listener. Local investigation only. |
| `ws stop` / `ws status` / `ws list` | Parser-visible stubs that return not implemented. |

Top-level `sora mcp stop` and `sora mcp discover` are **not registered commands**.

## Built-in server

```bash
# Implemented foreground path
sora mcp start --transport stdio

# Accepted by the parser, but currently raise NotImplementedError
sora mcp start --transport sse --port 3000
sora mcp start --transport streamable-http --port 3000
```

No `/sse` or `/mcp` HTTP endpoint is currently created.

## Save a stdio server record

```bash
sora mcp add filesystem \
  --command npx \
  --args -y @modelcontextprotocol/server-filesystem /absolute/allowed/path

sora mcp disable filesystem
sora mcp enable filesystem
sora mcp remove filesystem
```

Saving or enabling a record does not install its package, start it, verify its protocol, or prove that its credentials and permissions are safe.

## Experimental WebSocket listener

```bash
sora mcp ws start --host 127.0.0.1 --port 3001
```

The default host is `0.0.0.0`; do not use that default outside an isolated development environment. The listener is unauthenticated, incomplete, and does not provide the previously documented `ws://localhost:3000/ws` endpoint. See [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).