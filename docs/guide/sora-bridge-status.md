# SORA Bridge status

This page describes what the SORA bridge code currently does, what remains a control or preparation path, and which repository provides the live Gemini Discord voice runtime.

It is grounded in the current `sora_cli/voice.py`, provider client modules, `sora_api.py`, `plugins/sora_hermes/`, MCP implementation, VOIP plugin, TUI source, `sora_cli/main.py`, configuration helpers, and `pyproject.toml`.

## Plain-language summary

SORA Agent is a multi-provider companion and control layer. It has useful CLI, configuration, provider-preparation, Hermes-plugin, API, MCP, TUI, and VOIP surfaces, but several of those surfaces are intentionally classified as **PARTIAL** or **PROTOTYPE**:

- provider setup and the two provider command families do not share one canonical state model ([Issue #15](https://github.com/Capslockb/sora-agent/issues/15));
- the dashboard/control API is unauthenticated, can disclose secrets, and is unsafe to expose beyond a trusted local machine ([Issue #13](https://github.com/Capslockb/sora-agent/issues/13));
- stdio is the only implemented MCP server transport, while network/discovery paths are incomplete, unauthenticated, or heuristic ([Issue #16](https://github.com/Capslockb/sora-agent/issues/16));
- both checked-in VOIP startup entrypoints fail before constructing the current bridge runtime ([Issue #14](https://github.com/Capslockb/sora-agent/issues/14));
- the Ink/React TUI is a separately built prototype whose operational panels are not backed by canonical live state ([Issue #17](https://github.com/Capslockb/sora-agent/issues/17)).

SORA is **not yet a complete standalone replacement** for `Capslockb/gemini-live-discord-bridge` or the Hermes `discord-voice` runtime. Use the Gemini bridge repository when you need the currently documented live Discord/Gemini audio loop. Use this repository for SORA configuration, provider preparation, Hermes tools, stdio MCP work, and development toward a future SORA-owned media bridge.

## Current source of truth

| Area | Source of truth |
|---|---|
| Working Discord/Gemini voice runtime | `Capslockb/gemini-live-discord-bridge` and Hermes `discord-voice` |
| SORA CLI and command parser | `sora_cli/main.py` |
| Voice command handlers | `sora_cli/voice.py` |
| Provider-specific preparation/API clients | `sora_cli/*_client.py` |
| Configuration defaults/helpers | `sora_cli/config.py`, `sora_constants.py` |
| FastAPI backend | `sora_api.py` |
| MCP implementation and CLI | `sora_mcp.py`, `sora_cli/mcp.py` |
| Hermes SORA plugin | `plugins/sora_hermes/` |
| VOIP implementation | `plugins/sora_voip/`, `sora_cli/voip.py` |
| TUI source | `ui-tui/`, `sora_cli/main.py` |
| Package entrypoints | `pyproject.toml` |

## Current capability map

| Component | Status | Current behavior |
|---|---|---|
| `sora setup` / `sora setup --provider` | **PARTIAL** | Full voice setup directly configures Gemini Live and Vapi; quick paths mainly store credentials or identifiers and do not reliably select or enable providers. |
| `sora status` / `sora doctor` | **WORKING** | Implemented CLI diagnostics, but current `main` is not protected by active pytest CI. |
| `sora config` | **PARTIAL** | Config/env helper surface; secret-bearing output and positional secret handling remain constrained by [Issue #7](https://github.com/Capslockb/sora-agent/issues/7). |
| `sora providers ...` / `sora voice providers ...` | **PARTIAL** | Different registries, paths, provider coverage, and enable/disable semantics; neither is an authoritative runtime-health view. |
| `sora voice live/vapi/elevenlabs/openai/xai/ultravox/retell` | **PARTIAL** | Provider validation or preparation paths. Behavior differs by provider and does not itself prove a durable Discord media bridge. |
| `sora-api` / dashboard API | **PARTIAL — TRUSTED LOCAL ONLY** | Health, status, config, voice, provider, and MCP routes exist, but the API has no authentication, broad CORS, sensitive reads/mutations, and a default all-interface bind. |
| `sora mcp ...` | **PARTIAL** | stdio start reaches the checked-in server. Status/discovery use process/port heuristics; SSE and streamable HTTP are unimplemented; the raw WebSocket path is incomplete and unauthenticated. |
| `sora voice sip/ari/call/hangup/voip-*` | **PARTIAL — BLOCKED** | VOIP management/configuration surfaces exist, but the normal startup entrypoints cannot construct the checked-in bridge runtime. |
| `sora tui` | **PARTIAL — PROTOTYPE** | Requires a local build. Current operational panels contain simulated, hard-coded, fixed, random, or display-only values rather than canonical live state. |
| `plugins/sora_hermes` | **WORKING / PARTIAL RUNTIME** | Registers six Hermes tools that call SORA CLI paths; live Discord audio still depends on the external Hermes voice runtime. |

## Provider command reality

### `sora voice live`

The Gemini handler currently:

1. loads SORA config;
2. resolves Discord guild/user/channel defaults;
3. requires `guild_id` and `channel_id`;
4. checks `GEMINI_API_KEY` or `GOOGLE_API_KEY`;
5. checks `DISCORD_BOT_TOKEN`;
6. checks the `discord-voice` plugin flag and required Python voice dependencies;
7. returns a structured prerequisites-verified result.

It does **not** start the long-running Discord receive/playback and Gemini WebSocket loop by itself.

### Other voice providers

- `sora voice vapi` checks Discord targeting and credentials, then returns a preparation/start-status object; it does not supervise a durable Discord media session.
- `sora voice elevenlabs` resolves targeting, prepares a public or signed WebSocket URL, and returns redacted protocol metadata; it does not run Discord audio capture/playback.
- `sora voice openai` briefly connects to obtain an ephemeral key, disconnects, and returns readiness metadata; it does not retain the Realtime session.
- `sora voice xai` validates configuration and reports readiness; it does not connect a persistent media stream.
- `sora voice ultravox` creates a provider-side call and returns a shortened join URL; it does not connect that call to Discord.
- `sora voice retell` creates a provider-side web call and returns a call ID; it does not supervise the Discord media lifecycle.

A successful provider command may prove argument validation or provider-side resource preparation. It is not proof of active Discord audio.

### Status and stop

`sora voice status` currently reports SORA state rather than a durable bridge-process registry. `sora voice leave` returns a stop-status result, but durable process shutdown depends on future runtime integration.

## Dashboard and HTTP API reality

`sora-api` exposes a FastAPI server with route groups including:

- `/health` and `/api/status`;
- dashboard metrics and visualizer snapshots;
- `/api/voice/*` and `/api/providers/select`;
- `/api/config` and `/api/config/env`;
- `/api/mcp/*` and `/api/mcp/ws/*`.

The current API is a **trusted-local-development surface only**:

- `sora_api.py` defaults to `0.0.0.0:8080`;
- CORS allows all origins, methods, and headers;
- no route authentication or authorization is implemented;
- config/env routes can return stored configuration and actual secret-bearing values;
- voice, provider, config, and MCP mutations are unauthenticated;
- `/api/voice/start` stores intended state and returns `started` without launching a durable media process;
- `/api/mcp/start` and `/api/mcp/ws/start` store intended state and return `starting` without launching a supervised server.

Do not expose the API through a LAN bind, container port, tunnel, reverse proxy, Tailscale Serve/Funnel, or the public internet. `sora dashboard start --host 127.0.0.1` constrains only the FastAPI listener; the separately launched UI preview does not currently receive an explicit bind-host argument. See [Issue #13](https://github.com/Capslockb/sora-agent/issues/13).

## MCP reality

The built-in `sora mcp start --transport stdio` path reaches the checked-in MCP server. The rest of the surface must not be treated as an operational network service:

- accepted `sse` and `streamable-http` choices raise `NotImplementedError`;
- the separate raw WebSocket listener defaults to `0.0.0.0:3001`, has no authentication, and cannot complete tool calls as written;
- WebSocket stop/status/list commands are incomplete;
- setup and status detection infer MCP identity from ports/processes rather than a protocol handshake;
- API MCP start/stop routes save or report state but do not supervise a real server lifecycle.

Use `sora mcp catalog` as static metadata and `sora mcp status` as configuration/process/port diagnostics only. See [Issue #16](https://github.com/Capslockb/sora-agent/issues/16).

## VOIP and TUI reality

The VOIP package contains ARI, RTP, Dograh, call-state, and configuration components. However, both `sora voip start` and the installed `sora-voip` entrypoint import a nonexistent `VoipConfig` and call `VoipBridge` with the wrong construction contract. Do not use either command as release evidence until [Issue #14](https://github.com/Capslockb/sora-agent/issues/14) is fixed and exact-head lifecycle tests pass.

`sora tui` launches the checked-in Ink/React application only after a local build. Its voice, status, provider, doctor, benchmark, setup, configuration, and MCP panels currently use simulated or non-canonical values. Do not enter real credentials or use TUI output as operational evidence. See [Issue #17](https://github.com/Capslockb/sora-agent/issues/17).

## Hermes plugin reality

`plugins/sora_hermes` registers:

- `sora_voice_live`;
- `sora_voice_vapi`;
- `sora_voice_leave`;
- `sora_voice_status`;
- `sora_mcp_start`;
- `sora_mcp_status`.

The handlers call the SORA CLI through a subprocess. Because the underlying voice commands remain validation/control paths, the tools are not standalone production voice-runtime launchers. The MCP start tool is limited by the same stdio-only and lifecycle boundaries described above.

## Correct user flows today

### Working live Gemini voice in Discord

Use the Gemini bridge repository and the Hermes `discord-voice` runtime:

```bash
git clone https://github.com/Capslockb/gemini-live-discord-bridge.git
cd gemini-live-discord-bridge
./install.sh
systemctl --user restart hermes-gateway
```

Then use the bridge's documented Discord command.

### Configure SORA or inspect provider preparation

```bash
pipx install git+https://github.com/Capslockb/sora-agent
sora setup
sora status
sora doctor
sora providers list
sora voice providers list
sora mcp catalog
```

Treat setup/provider results as non-canonical diagnostics while Issue #15 remains open, and treat MCP catalog/status output as metadata or heuristics rather than protocol-health evidence.

For API development, run only on a trusted local machine and apply the Issue #13 exposure boundary. Do not use raw `sora-api` defaults as a safe network deployment recipe.

## Validation boundary and roadmap

The last recorded local pytest result was 24/24 on PR #5. The staged workflow remains outside `.github/workflows/`, so current `main` and pull requests are not automatically pytest-verified. See [Issue #12](https://github.com/Capslockb/sora-agent/issues/12).

Current high-priority roadmap blockers are:

1. activate exact-head pytest CI (Issue #12);
2. secure both dashboard listeners and redact secrets (Issue #13);
3. repair VOIP construction and lifecycle (Issue #14);
4. unify provider setup and state (Issue #15);
5. make MCP transports, discovery, and lifecycle truthful and secure (Issue #16);
6. choose and implement a deterministic prototype or live-state TUI contract (Issue #17);
7. complete CLI secret-handling and deterministic-build work (Issue #7).

Until those items are resolved, documentation must distinguish configuration, provider-side readiness, saved state, and simulated UI output from an active authenticated runtime.