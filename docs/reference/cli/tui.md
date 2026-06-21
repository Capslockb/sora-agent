# sora tui

Launch the Terminal UI.

## Status

**PLANNED**

## Usage

```bash
sora tui         # Currently falls back to chat REPL
sora tui --build # Planned: build Ink/React bundle
```

## Current behavior

The current implementation is a chat REPL fallback. A real Ink/React TUI with voice panels, provider management, status dashboard, and benchmark runner is planned for a future release.

## Verification

```bash
sora tui
```

Expected: a text REPL prompt, not a graphical TUI.

## Notes

- Do not screenshot or demo `sora tui` as a finished product.
- The UI skin system (`sora_cli/skin_engine.py`) is implemented, but the TUI renderer is not.
