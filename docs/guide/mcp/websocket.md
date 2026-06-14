# WebSocket MCP

S0RA includes a native WebSocket MCP server for real-time tool access.

## Start Server

```bash
# HTTP + WebSocket (recommended)
sora mcp start --transport streamable-http --port 3000

# SSE
sora mcp start --transport sse --port 3000

# Stdio only (for CLI tools)
sora mcp start --transport stdio
```

## Connection

| Transport | Endpoint |
|-----------|----------|
| Streamable HTTP | `http://localhost:3000/mcp` |
| SSE | `http://localhost:3000/sse` |
| WebSocket | `ws://localhost:3000/ws` |

## Client Examples

### Python

```python
import asyncio
from mcp import ClientSession, StdioServerParameters

async def main():
    async with ClientSession(
        "http://localhost:3000/mcp"
    ) as session:
        tools = await session.list_tools()
        print(tools)
        
        result = await session.call_tool("filesystem_read", {"path": "/tmp/test.txt"})
        print(result)

asyncio.run(main())
```

### JavaScript

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

const client = new Client(
  { name: "my-client", version: "1.0.0" },
  { transport: new StreamableHTTPClientTransport("http://localhost:3000/mcp") }
);

await client.connect();
const tools = await client.listTools();
```
