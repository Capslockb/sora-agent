# Profiles

S0RA supports multiple isolated configuration profiles, mirroring Hermes.

## Profile Directory Structure

```
~/.sora/                    # Default profile
~/.sora-profiles/
  ├── work/                 # Work profile
  ├── personal/             # Personal profile
  └── testing/              # Testing profile
~/.sora-<name>/             # Alternative (Hermes-style)
```

## Creating Profiles

```bash
# Via CLI
sora config profile create work

# Via environment
export SORA_HOME=~/.sora-work
sora setup
```

## Profile Switching

```bash
# One-off command
sora --profile work voice live

# Persistent for session
export SORA_HOME=~/.sora-work
sora chat

# List all profiles
sora config profiles
```

## Profile Isolation

Each profile has its own:
- `config.yaml`
- `.env` (secrets)
- `plugins/` directory
- `skins/` directory
- `logs/` directory
- `memory/` (Honcho local)

## Use Cases

| Profile | Purpose |
|---------|---------|
| `default` | Main personal assistant |
| `work` | Work Discord + work Asterisk |
| `testing` | Experiment with providers |
| `production` | Stable config for deployment |
