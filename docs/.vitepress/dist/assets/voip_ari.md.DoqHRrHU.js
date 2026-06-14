import{_ as a,o as n,c as i,a2 as p}from"./chunks/framework.DqgtWGRo.js";const k=JSON.parse('{"title":"ARI Configuration","description":"","frontmatter":{},"headers":[],"relativePath":"voip/ari.md","filePath":"voip/ari.md"}'),e={name:"voip/ari.md"};function l(t,s,h,o,r,c){return n(),i("div",null,[...s[0]||(s[0]=[p(`<h1 id="ari-configuration" tabindex="-1">ARI Configuration <a class="header-anchor" href="#ari-configuration" aria-label="Permalink to &quot;ARI Configuration&quot;">​</a></h1><p>ARI (Asterisk REST Interface) is the control channel for call management.</p><h2 id="connection" tabindex="-1">Connection <a class="header-anchor" href="#connection" aria-label="Permalink to &quot;Connection&quot;">​</a></h2><div class="language-bash vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">bash</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># Connect ARI app</span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">sora</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> voice</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> ari</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> connect</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> --app</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> sora-bridge</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># Check status</span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">sora</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> voice</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> ari</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> status</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># List registered apps</span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">sora</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> voice</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> ari</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> apps</span></span></code></pre></div><h2 id="app-registration" tabindex="-1">App Registration <a class="header-anchor" href="#app-registration" aria-label="Permalink to &quot;App Registration&quot;">​</a></h2><p>The <code>sora-bridge</code> app is registered when the bridge starts. In <code>ari.conf</code>:</p><div class="language-ini vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">ini</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">[general]</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">enabled</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> = yes</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">[sora]</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">type</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> = user</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">read_only</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> = no</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">password</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> = secure-password</span></span></code></pre></div><h2 id="event-flow" tabindex="-1">Event Flow <a class="header-anchor" href="#event-flow" aria-label="Permalink to &quot;Event Flow&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>Inbound Call</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>StasisStart (channel enters app)</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>ARI: answer channel</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>ARI: externalMedia (RTP to Sora)</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>Dograh sessionStart</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>Conversation (RTP ↔ Dograh)</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>Hangup / StasisEnd</span></span>
<span class="line"><span>    │</span></span>
<span class="line"><span>    ▼</span></span>
<span class="line"><span>Cleanup (RTP stop, Dograh sessionEnd)</span></span></code></pre></div><h2 id="outbound-calls" tabindex="-1">Outbound Calls <a class="header-anchor" href="#outbound-calls" aria-label="Permalink to &quot;Outbound Calls&quot;">​</a></h2><div class="language-bash vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">bash</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">sora</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> voice</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> call</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;+155****4567&quot;</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> --caller-id</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;Sora&quot;</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> --auto-answer</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> --record</span></span></code></pre></div><p>Flow:</p><ol><li>ARI <code>originate</code> to <code>PJSIP/+155****4567</code></li><li>Channel enters <code>sora-bridge</code> app (with <code>outbound,callId</code> args)</li><li>Same flow as inbound</li></ol>`,13)])])}const g=a(e,[["render",l]]);export{k as __pageData,g as default};
