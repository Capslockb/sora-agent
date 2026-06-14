import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'S0RA Agent',
  description: 'Standalone Hermes-like CLI for Gemini Live, Vapi, ElevenLabs, and VOIP (Asterisk + Dograh) voice bridges',
  lang: 'en-US',
  base: '/sora-agent/',
  head: [
    ['link', { rel: 'icon', href: '/sora-agent/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#a855f7' }],
  ],

  themeConfig: {
    logo: '/sora-agent/favicon.svg',
    siteTitle: 'S0RA Agent',

    nav: [
      { text: 'Guide', link: '/guide/', activeMatch: '^/guide/' },
      { text: 'Reference', link: '/reference/cli', activeMatch: '^/reference/' },
      { text: 'VOIP', link: '/voip/setup', activeMatch: '^/voip/' },
      { text: 'GitHub', link: 'https://github.com/Capslockb/sora-agent' },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Introduction',
          items: [
            { text: 'What is S0RA?', link: '/guide/' },
            { text: 'Quick Start', link: '/guide/quick-start' },
            { text: 'Installation', link: '/guide/installation' },
            { text: 'Configuration', link: '/guide/configuration' },
          ],
        },
        {
          text: 'Core Concepts',
          items: [
            { text: 'Architecture', link: '/guide/architecture' },
            { text: 'Profiles', link: '/guide/profiles' },
            { text: 'Plugins', link: '/guide/plugins' },
            { text: 'Skins & Theming', link: '/guide/skins' },
          ],
        },
        {
          text: 'Voice Bridges',
          items: [
            { text: 'Discord: Gemini Live', link: '/guide/voice/gemini-live' },
            { text: 'Discord: Vapi.ai', link: '/guide/voice/vapi' },
            { text: 'Discord: ElevenLabs', link: '/guide/voice/elevenlabs' },
            { text: 'Provider Toggle', link: '/guide/voice/providers' },
          ],
        },
        {
          text: 'MCP Integration',
          items: [
            { text: 'MCP Servers', link: '/guide/mcp/servers' },
            { text: 'Auto-Discovery', link: '/guide/mcp/auto-discovery' },
            { text: 'WebSocket MCP', link: '/guide/mcp/websocket' },
          ],
        },
      ],
      '/reference/': [
        {
          text: 'CLI Reference',
          items: [
            { text: 'Commands Overview', link: '/reference/cli' },
            { text: 'sora', link: '/reference/cli/sora' },
            { text: 'sora chat', link: '/reference/cli/chat' },
            { text: 'sora setup', link: '/reference/cli/setup' },
            { text: 'sora voice', link: '/reference/cli/voice' },
            { text: 'sora mcp', link: '/reference/cli/mcp' },
            { text: 'sora config', link: '/reference/cli/config' },
            { text: 'sora plugins', link: '/reference/cli/plugins' },
            { text: 'sora doctor', link: '/reference/cli/doctor' },
            { text: 'sora tui', link: '/reference/cli/tui' },
          ],
        },
        {
          text: 'Plugins',
          items: [
            { text: 'sora-hermes', link: '/reference/plugins/sora-hermes' },
            { text: 'sora-voip', link: '/reference/plugins/sora-voip' },
          ],
        },
        {
          text: 'Configuration',
          items: [
            { text: 'config.yaml', link: '/reference/config/yaml' },
            { text: 'Environment Variables', link: '/reference/config/env' },
            { text: 'Profiles', link: '/reference/config/profiles' },
          ],
        },
      ],
      '/voip/': [
        {
          text: 'VOIP Integration',
          items: [
            { text: 'Overview', link: '/voip/' },
            { text: 'Asterisk Setup', link: '/voip/asterisk' },
            { text: 'Dograh/Gemini Live', link: '/voip/dograh' },
            { text: 'SIP Configuration', link: '/voip/sip' },
            { text: 'ARI Configuration', link: '/voip/ari' },
            { text: 'Call Commands', link: '/voip/commands' },
            { text: 'Recording', link: '/voip/recording' },
            { text: 'Troubleshooting', link: '/voip/troubleshooting' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Capslockb/sora-agent' },
    ],

    footer: {
      message: 'Released under MIT License.',
      copyright: 'Copyright © 2026 Capslockb',
    },

    editLink: {
      pattern: 'https://github.com/Capslockb/sora-agent/edit/main/docs/:path',
      text: 'Edit this page on GitHub',
    },

    search: {
      provider: 'local',
    },

    outline: {
      level: [2, 3],
    },
  },

  vite: {
    optimizeDeps: {
      include: ['vue'],
    },
  },
  ignoreDeadLinks: true,
})