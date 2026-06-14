# Installation Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11 - 3.13 | pipx handles venv |
| Node.js | 18+ | For TUI build & dashboard |
| Git | Any | For git-based updates |
| pipx | Latest | `pip install pipx` |

## Install Methods

### pipx (Recommended)

```bash
# Install pipx if needed
pip install pipx
pipx ensurepath

# Install S0RA
pipx install git+https://github.com/Capslockb/sora-agent

# Verify
sora --version
sora --help
```

### Development Install

```bash
git clone https://github.com/Capslockb/sora-agent
cd sora-agent

# Core CLI
pip install -e .

# With TUI (requires Node.js)
cd ui-tui && npm install && npm run build && cd ..

# With Dashboard
cd website && npm install && npm run build && cd ..

# With VOIP plugin
pip install -e ./plugins/sora_voip
```

### Docker (Optional)

```dockerfile
FROM python:3.12-slim
RUN pip install pipx && pipx ensurepath
RUN pipx install git+https://github.com/Capslockb/sora-agent
ENV PATH="/root/.local/bin:${PATH}"
ENTRYPOINT ["sora"]
```

## Post-Install

```bash
# Enable shell completions
sora --install-completion

# Verify all components
sora doctor

# Update to latest
sora update
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `command not found: sora` | Run `pipx ensurepath` and restart shell |
| Python version error | Use `pipx install --python python3.11 ...` |
| TUI build fails | Ensure Node.js 18+ and run `cd ui-tui && npm install` |
| Discord voice fails | Check `DISCORD_BOT_TOKEN` and gateway intents |
