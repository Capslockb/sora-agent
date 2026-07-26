# Installation Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11 - 3.14 | The package metadata permits this range. The staged pytest workflow currently targets only Python 3.12 and 3.13. |
| Node.js | `^20.19.0`, `^22.12.0`, or `>=24.0.0` | Required only for the dashboard and TUI sources. The checked-in dashboard dependency tree does not support the previously documented Node.js 18 baseline. |
| Git | Any current version | Required for source installs and git-based updates. |
| pipx | Current release | Recommended for an isolated CLI installation. |

## Install Methods

### pipx (Recommended)

```bash
# Install pipx if needed
python -m pip install --user pipx
pipx ensurepath

# Install S0RA
pipx install git+https://github.com/Capslockb/sora-agent

# Verify the installed command surface
sora --version
sora --help
```

Restart the shell after `pipx ensurepath` if `sora` is not found.

### Development Install

```bash
git clone https://github.com/Capslockb/sora-agent
cd sora-agent

# Install the root Python project, including the checked-in plugin packages
python -m pip install -e .

# Build the dashboard reproducibly from its lockfile
npm --prefix website ci
npm --prefix website run build
```

The VOIP plugin is part of the root project and is **not** a standalone package at `plugins/sora_voip`; do not run `pip install -e ./plugins/sora_voip`. Installation also does not resolve the current VOIP construction blocker tracked in [Issue #14](https://github.com/Capslockb/sora-agent/issues/14).

The TUI remains a prototype with inconsistent checked-in build entrypoints. Do not treat `npm run build` or `sora tui --build` as reproducible release validation until [Issue #17](https://github.com/Capslockb/sora-agent/issues/17) is resolved.

The dashboard frontend can be built locally, but its control API is currently a trusted-local-development surface. Keep it loopback-only and do not expose it to a LAN or the internet; see [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).

### Docker (Core CLI Only)

```dockerfile
FROM python:3.12-slim
RUN python -m pip install --no-cache-dir pipx
ENV PATH="/root/.local/bin:${PATH}"
RUN pipx install git+https://github.com/Capslockb/sora-agent
ENTRYPOINT ["sora"]
```

This minimal image installs the Python CLI. It does not build the dashboard or TUI assets and does not make the blocked VOIP lifecycle operational.

## Post-Install

```bash
# Inspect the registered commands
sora --help

# Run the built-in diagnostic command
sora doctor

# Show component status
sora status

# Update a git-based installation
sora update
```

The CLI does not currently implement `sora --install-completion`; do not use that command as an installation step.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `command not found: sora` | Run `pipx ensurepath`, restart the shell, and verify that the pipx binary directory is on `PATH`. |
| Python version error | Use a supported interpreter explicitly, for example `pipx install --python python3.12 git+https://github.com/Capslockb/sora-agent`. |
| Dashboard dependency or build error | Use a supported Node.js version and run `npm --prefix website ci` before `npm --prefix website run build`. |
| TUI build fails | Treat the TUI as a prototype and follow [Issue #17](https://github.com/Capslockb/sora-agent/issues/17); changing Node.js versions alone does not resolve the inconsistent build entrypoints. |
| VOIP start fails | Installation is not the blocker; follow [Issue #14](https://github.com/Capslockb/sora-agent/issues/14). |
| Discord voice fails | Check `DISCORD_BOT_TOKEN`, required gateway intents, and the provider-specific voice documentation. |
