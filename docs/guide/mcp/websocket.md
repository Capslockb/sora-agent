# MCP Transport Status

S0RA's checked-in MCP runtime is only implemented for **stdio**. The CLI exposes additional transport and WebSocket commands, but they are incomplete and must not be treated as production network servers.

## Implemented path

```bash
sora mcp start --transport stdio
```

This runs the built-in MCP server over the process standard-input/standard-output streams. It remains a foreground process and stops when that process exits.

## Parser-visible but unimplemented transports

These commands are accepted by the CLI parser, but the server immediately raises `NotImplementedError`:

```bash
sora mcp start --transport sse --port 3000
sora mcp start --transport streamable-http --port 3000
```

The previously documented `/sse` and `/mcp` HTTP endpoints therefore do not exist in the current runtime.

## Experimental custom WebSocket path

```bash
sora mcp ws start --host 127.0.0.1 --port 3001
```

The custom WebSocket listener is separate from `sora mcp start`. Its current limitations are material:

- the default bind address is `0.0.0.0`, so always pass `--host 127.0.0.1` during local investigation;
- it has no authentication or authorization boundary;
- it implements only a partial raw JSON `tools/call` shape rather than a complete MCP session lifecycle;
- the checked-in tool-call handler references state that is not available in the handler, so calls cannot complete as written;
- `sora mcp ws stop`, `status`, and `list` are stubs;
- there is no supported `ws://localhost:3000/ws` endpoint.

Do not publish this listener through a LAN, tunnel, container port, reverse proxy, or the public internet. Do not use it for credentials, private tool data, or production automation.

The runtime, lifecycle, discovery, and security corrections are tracked in [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).