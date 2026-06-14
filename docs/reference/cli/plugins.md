# sora plugins

Plugin management (mirrors Hermes plugin system).

```bash
sora plugins <SUBCOMMAND>
```

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all plugins (bundled + user) |
| `enable NAME` | Enable plugin |
| `disable NAME` | Disable plugin |
| `install REPO` | Install from GitHub |
| `remove NAME` | Remove plugin |
| `update` | Update all Git plugins |

## Built-in Plugins

| Plugin | Description |
|--------|-------------|
| `sora-hermes` | Discord voice bridges |
| `sora-voip` | Asterisk + Dograh VOIP |
| `mcp` | MCP integration |
| `honcho` | Honcho memory |

## Example

```bash
sora plugins list
sora plugins enable sora-voip
sora plugins install user/my-plugin
sora plugins update
```