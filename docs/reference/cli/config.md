# sora config

Configuration management.

```bash
sora config <SUBCOMMAND>
```

## Commands

| Command | Description |
|---------|-------------|
| `show` | Show current config (secrets masked) |
| `set KEY VAL` | Set config value |
| `get KEY` | Get config value |
| `profiles` | List profiles |
| `profile` | Profile management |
| `reset` | Reset to defaults |

## Examples

```bash
sora config show
sora config set model.temperature 0.8
sora config get voice.gemini_live.voice
sora config profile create work
sora config profile switch work
```