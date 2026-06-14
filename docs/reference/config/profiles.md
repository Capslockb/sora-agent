# Profile Configuration

## Directory Structure

```
~/.sora/                    # Default profile
├── config.yaml
├── .env
├── plugins/
├── skins/
└── logs/

~/.sora-profiles/
├── work/
│   ├── config.yaml
│   ├── .env
│   └── ...
├── personal/
└── testing/
```

## Creating Profiles

```bash
# CLI
sora config profile create work

# Manual
mkdir -p ~/.sora-profiles/work
cp ~/.sora/config.yaml ~/.sora-profiles/work/
cp ~/.sora/.env ~/.sora-profiles/work/
```

## Switching Profiles

```bash
# One-off
sora --profile work voice live

# Persistent
export SORA_HOME=~/.sora-profiles/work
sora chat

# List
sora config profiles
```

## Profile Isolation

Each profile has completely separate:
- `config.yaml` — all settings
- `.env` — all secrets
- `plugins/` — enabled plugins
- `skins/` — custom skins
- `logs/` — log files
- Honcho local memory (if enabled)

## Use Cases

| Profile | Config |
|---------|--------|
| `default` | Personal Discord + personal Asterisk |
| `work` | Work Discord + work Asterisk + work Dograh |
| `testing` | All providers enabled, debug logging |
| `production` | Minimal providers, stable config |
