# Call Recording

## Configuration

```yaml
voip:
  record_calls: true          # Record all calls by default
  recording_dir: "~/.sora/recordings"
```

## Per-Call Recording

```bash
# Record specific call
sora voice call "+1555..." --record

# Don't record (if default is true)
sora voice call "+1555..." --no-record  # Not yet implemented
```

## Recording Format

| Property | Value |
|----------|-------|
| Format | WAV |
| Sample Rate | 48 kHz |
| Channels | 1 (mono, mixed) |
| Bit Depth | 16-bit |
| Filename | `{call_id}_{caller}_{called}_{timestamp}.wav` |

## Storage

```bash
# List recordings
ls -la ~/.sora/recordings/

# Play
aplay ~/.sora/recordings/abc123_...wav

# Convert to MP3
ffmpeg -i recording.wav recording.mp3
```

## Privacy

- Recordings stored locally only
- No cloud upload unless you configure it
- GDPR/CCPA: implement your own retention policy
