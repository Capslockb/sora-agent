# Skins & Theming

S0RA includes a skin engine compatible with Hermes.

## Built-in Skins

| Skin | Description |
|------|-------------|
| `sora` | Default S0RA theme (purple/pink gradient) |
| `sora-dark` | Dark variant |
| `minimal` | Clean, minimal output |
| `hermes` | Hermes-compatible theme |

## Applying Skins

```bash
# Via config
display:
  skin: sora-dark

# Via CLI flag
sora --skin minimal chat

# Via env var
SORA_SKIN=hermes sora chat
```

## Custom Skins

Create YAML in `~/.sora/skins/my-skin.yaml`:

```yaml
name: My Skin
extends: sora          # optional base

colors:
  primary: "#a855f7"   # purple
  secondary: "#ec4899" # pink
  success: "#22c55e"
  warning: "#f59e0b"
  error: "#ef4444"
  background: "#0f0f0f"
  surface: "#1a1a1a"
  text: "#fafafa"
  muted: "#71717a"

styles:
  header: "bold {primary}"
  info: "{primary}"
  success: "bold {success}"
  warning: "bold {warning}"
  error: "bold {error}"
  dim: "dim {muted}"
  code: "bg:#2a2a2a {primary}"
  link: "underline {primary}"

icons:
  success: "✓"
  error: "✗"
  warning: "⚠"
  info: "ℹ"
  arrow: "→"
  bullet: "•"
```

## Skin Inheritance

```yaml
# Extend and override
extends: sora
colors:
  primary: "#06b6d4"  # cyan instead of purple
```

## Preview Skins

```bash
sora doctor --skin-preview
# Shows all skins with example output
```
