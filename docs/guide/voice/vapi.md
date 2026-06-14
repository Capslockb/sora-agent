# Vapi.ai (Discord)

## Overview

[Vapi.ai](https://vapi.ai) managed conversational AI platform. Handles phone, web, Discord via dashboard. S0RA bridges Discord voice to your Vapi assistant.

## Requirements

| Requirement | Details |
|-------------|---------|
| `VAPI_API_KEY` | From [dashboard.vapi.ai/api-keys](https://dashboard.vapi.ai/api-keys) |
| `DISCORD_BOT_TOKEN` | Bot with Voice intents |
| Vapi Assistant | Create at [dashboard.vapi.ai](https://dashboard.vapi.ai) |

## Configuration

```bash
sora setup
# Section: Voice Bridges → Vapi.ai
```

```yaml
voice:
  vapi:
    enabled: true
    assistant_id: "your-assistant-id"
    phone_number_id: ""  # Optional for phone calls
  discord:
    guild_id: "..."
    default_user_id: "..."
```

## Start Bridge

```bash
sora voice vapi
# or
sora voice vapi --guild <ID> --channel <ID>
```

## Assistant Configuration

In Vapi Dashboard:
1. Create Assistant → Choose model (GPT-4, Claude, etc.)
2. Add Functions → Webhook to your backend
3. Set Voice → ElevenLabs, OpenAI, etc.
4. Copy `assistant_id` to S0RA config

## Phone Numbers

```bash
# Configure phone number in Vapi Dashboard
# Add to S0RA config
voice:
  vapi:
    phone_number_id: "pn_..."
```

## Multi-Assistant

Create multiple assistants in Vapi, switch via:

```bash
# Not yet implemented — planned for v0.2
# sora voice vapi --assistant <ID>
```
