# MCP Detection Heuristics

S0RA does **not** currently perform protocol-verified MCP auto-discovery.

## What setup checks

During the MCP section of `sora setup`, the wizard:

- attempts TCP connections to `127.0.0.1` ports 3000–3010;
- assigns a fixed MCP server name to each open port without an MCP handshake;
- on Unix-like systems, uses `pgrep` and `ps` to look for a small set of command-name fragments;
- may offer to save the resulting heuristic record.

It does not inspect `~/.mcp.json` or project `.mcp.json` files, and it does not prove server identity, protocol compatibility, tool availability, authentication, or health.

Any unrelated application listening on a mapped port can be reported as a named MCP server. Process detection is platform-dependent and can silently produce no results where `pgrep` or `ps` is unavailable.

## Persistence warning

A port-derived result can lack the command and argument fields used by normal stdio server records. Do not accept a detected entry until you have independently identified the process and can reconstruct a complete, least-privilege configuration.

Prefer adding a reviewed command explicitly:

```bash
sora mcp add filesystem \
  --command npx \
  --args -y @modelcontextprotocol/server-filesystem /absolute/allowed/path
```

## Manual inspection

```bash
sora mcp status
```

This command uses similar process/listener heuristics and must not be treated as a protocol health check.

There is no registered `sora mcp discover` command. Verified discovery, cross-platform behavior, and safe persistence are tracked in [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).