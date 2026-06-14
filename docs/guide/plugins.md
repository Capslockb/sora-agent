# Plugins

S0RA uses the same plugin architecture as Hermes.

## Built-in Plugins

| Plugin | Description | Enabled By Default |
|--------|-------------|-------------------|
| `sora-hermes` | Discord voice bridges (Gemini Live, Vapi, ElevenLabs) | Yes |
| `sora-voip` | Asterisk ARI + Dograh/Gemini Live for phone calls | No |
| `mcp` | MCP server integration | Yes |
| `honcho` | Honcho memory integration | Yes |

## Plugin Structure

```
~/.sora/plugins/
  my-plugin/
    ├── plugin.yaml          # Manifest
    ├── __init__.py          # Entry point with register(ctx)
    └── plugin_icon.svg      # Optional
```

## plugin.yaml

```yaml
name: my-plugin
version: 1.0.0
description: My awesome plugin
author: Me
entry_point: my_plugin
min_sora_version: "0.1.0"
config_schema:
  my_setting:
    type: string
    default: "value"
    description: A setting
```

## Plugin Entry Point

```python
# my_plugin/__init__.py
from sora_cli.plugins import ToolSpec, PluginContext

def register(ctx: PluginContext):
    # Register CLI tool
    ctx.register_tool(ToolSpec(
        name="my_tool",
        description="Does something cool",
        module="my_plugin.tools",
        function="my_tool_func"
    ))
    
    # Register Discord slash command
    ctx.register_slash_command({
        "name": "my-cmd",
        "description": "My command",
        "handler": "my_plugin.commands.my_cmd"
    })
```

## Managing Plugins

```bash
# List all plugins
sora plugins list

# Enable/disable
sora plugins enable sora-voip
sora plugins disable sora-hermes

# Install from GitHub
sora plugins install user/repo

# Update all
sora plugins update

# Remove
sora plugins remove my-plugin
```

## Developing Plugins

1. Create directory: `~/.sora/plugins/my-plugin/`
2. Add `plugin.yaml` and `__init__.py`
3. Run `sora plugins enable my-plugin`
4. Test: `sora my-tool`
