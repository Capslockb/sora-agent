import{_ as a,o as n,c as e,a2 as i}from"./chunks/framework.DqgtWGRo.js";const g=JSON.parse('{"title":"Architecture","description":"","frontmatter":{},"headers":[],"relativePath":"guide/architecture.md","filePath":"guide/architecture.md"}'),t={name:"guide/architecture.md"};function p(l,s,r,o,c,d){return n(),e("div",null,[...s[0]||(s[0]=[i(`<h1 id="architecture" tabindex="-1">Architecture <a class="header-anchor" href="#architecture" aria-label="Permalink to &quot;Architecture&quot;">​</a></h1><h2 id="high-level-overview" tabindex="-1">High-Level Overview <a class="header-anchor" href="#high-level-overview" aria-label="Permalink to &quot;High-Level Overview&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>┌─────────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                        S0RA Agent CLI                           │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│  Constants  │  Config  │  Logging  │  Profiles  │  Skins  │     │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                    Plugin Manager                               │</span></span>
<span class="line"><span>│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │</span></span>
<span class="line"><span>│  │ sora-hermes  │  │  sora-voip   │  │      built-in        │  │</span></span>
<span class="line"><span>│  │  (Discord)   │  │ (Asterisk)   │  │  (MCP, Memory, etc)  │  │</span></span>
<span class="line"><span>│  └──────────────┘  └──────────────┘  └──────────────────────┘  │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│  Voice Layer  │  MCP Layer  │  Memory Layer  │  Tool Layer    │</span></span>
<span class="line"><span>└─────────────────────────────────────────────────────────────────┘</span></span></code></pre></div><h2 id="core-modules" tabindex="-1">Core Modules <a class="header-anchor" href="#core-modules" aria-label="Permalink to &quot;Core Modules&quot;">​</a></h2><table tabindex="0"><thead><tr><th>Module</th><th>Path</th><th>Purpose</th></tr></thead><tbody><tr><td>Constants</td><td><code>sora_constants/</code></td><td>Paths, defaults, version</td></tr><tr><td>Config</td><td><code>sora_cli/config.py</code></td><td>YAML + env merge, profiles</td></tr><tr><td>Logging</td><td><code>sora_logging/</code></td><td>Structured, colored, file+stdout</td></tr><tr><td>Profiles</td><td><code>sora_cli/profile.py</code></td><td>Isolated config directories</td></tr><tr><td>Skins</td><td><code>sora_cli/skin.py</code></td><td>Theme engine (YAML + built-in)</td></tr><tr><td>Plugins</td><td><code>sora_cli/plugins.py</code></td><td>Discovery, enable/disable, YAML</td></tr></tbody></table><h2 id="voice-architecture" tabindex="-1">Voice Architecture <a class="header-anchor" href="#voice-architecture" aria-label="Permalink to &quot;Voice Architecture&quot;">​</a></h2><h3 id="discord-voice-bridges" tabindex="-1">Discord Voice Bridges <a class="header-anchor" href="#discord-voice-bridges" aria-label="Permalink to &quot;Discord Voice Bridges&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>Discord Gateway (Voice WS)</span></span>
<span class="line"><span>       │</span></span>
<span class="line"><span>       ▼</span></span>
<span class="line"><span>┌──────────────────┐</span></span>
<span class="line"><span>│  sora-hermes     │  Plugin</span></span>
<span class="line"><span>│  bridge.py       │  → VoiceLiveBridge</span></span>
<span class="line"><span>│  LiveAudioSource │  → Discord AudioSource</span></span>
<span class="line"><span>│  VoiceListener   │  → Opus → PCM → Gemini</span></span>
<span class="line"><span>└──────────────────┘</span></span>
<span class="line"><span>       │</span></span>
<span class="line"><span>       ▼</span></span>
<span class="line"><span>Gemini Live API (WSS)</span></span></code></pre></div><h3 id="voip-bridge-asterisk-dograh" tabindex="-1">VOIP Bridge (Asterisk + Dograh) <a class="header-anchor" href="#voip-bridge-asterisk-dograh" aria-label="Permalink to &quot;VOIP Bridge (Asterisk + Dograh)&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>Asterisk (SIP/RTP)          Dograh/Gemini Live</span></span>
<span class="line"><span>       │                          │</span></span>
<span class="line"><span>       ▼                          ▼</span></span>
<span class="line"><span>┌──────────────────────────────────────────┐</span></span>
<span class="line"><span>│         sora-voip Plugin                 │</span></span>
<span class="line"><span>│  ┌──────────┐  ┌─────────┐  ┌──────────┐ │</span></span>
<span class="line"><span>│  │ ARI      │  │  RTP    │  │ Dograh   │ │</span></span>
<span class="line"><span>│  │ Client   │◄─┤ Handler │──►│ Client   │ │</span></span>
<span class="line"><span>│  └──────────┘  └─────────┘  └──────────┘ │</span></span>
<span class="line"><span>└──────────────────────────────────────────┘</span></span></code></pre></div><h2 id="mcp-layer" tabindex="-1">MCP Layer <a class="header-anchor" href="#mcp-layer" aria-label="Permalink to &quot;MCP Layer&quot;">​</a></h2><ul><li><strong>Auto-discovery</strong>: Scans ports 3000-3010 + stdio processes</li><li><strong>WebSocket MCP</strong>: Native WS server on port 3000 (configurable)</li><li><strong>CLI Management</strong>: <code>sora mcp start/status/stop/catalog</code></li></ul><h2 id="plugin-system" tabindex="-1">Plugin System <a class="header-anchor" href="#plugin-system" aria-label="Permalink to &quot;Plugin System&quot;">​</a></h2><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># plugin.yaml</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">name: my</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">-</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">plugin</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">version: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">1.0</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">.0</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">description: My plugin</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">entry_point: my_plugin</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># my_plugin/__init__.py</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> register</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(ctx):</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ctx.register_tool(my_tool)</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ctx.register_slash_command(my_command)</span></span></code></pre></div>`,14)])])}const u=a(t,[["render",p]]);export{g as __pageData,u as default};
