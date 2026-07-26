# sora tui

Launch the checked-in Ink/React terminal prototype.

## Status

**PARTIAL — PROTOTYPE**

The command is registered and can launch the `ui-tui` application after it has been built. It does **not** fall back to the chat REPL.

The current interface is not a live management or health surface. Several panels use simulated, random, fixed, or display-only data rather than canonical CLI/API/runtime state. Track the runtime and build correction in [Issue #17](https://github.com/Capslockb/sora-agent/issues/17).

## Usage

```bash
sora tui          # Launch ui-tui/dist/cli.js when it exists
sora tui --build  # Build, then launch the terminal prototype
```

If the bundle is missing, plain `sora tui` exits with:

```text
TUI not built. Run 'sora tui --build' first.
```

## Current behavior

The prototype renders Ink/React panels for voice, MCP, providers, status, configuration, doctor, setup, and benchmarks. These labels must not be interpreted as verified live operations:

- voice connect/disconnect changes local UI state and emits simulated log messages;
- status and provider values are hard-coded;
- doctor returns fixed sample results after a timer;
- benchmark values are randomly generated;
- setup and configuration panels do not apply a complete canonical configuration;
- the MCP panel includes commands and transports that do not match the verified MCP contract in [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).

The Python build path also uses `npm install` and `npx esbuild` despite the checked-in lockfile. Deterministic, no-download build execution remains required under [Issue #7](https://github.com/Capslockb/sora-agent/issues/7).

## Safe verification

```bash
sora tui
```

Expected without a checked-in or locally built bundle: a controlled “TUI not built” error.

A locally built interface may be used only as a prototype preview. Do not use its status, doctor, benchmark, provider, setup, voice, or MCP output as operational evidence.

## Notes

- Do not screenshot or demo the current TUI as a finished control surface without an explicit prototype/simulated-data label.
- Do not enter or display real credentials in the prototype.
- The setup wizard's curses helpers in `sora_cli/curses_ui.py` are separate from the Ink/React `sora tui` application.
- Completion requires one aligned build contract, truthful UI labels, deterministic tests, and either real state integration or unavoidable prototype labeling.