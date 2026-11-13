# Claude Code Voice

A Claude Code plugin that gives Claude a persona and a voice. While Claude works, it writes short status lines such as "Reading the config, then running the tests", and the plugin speaks them aloud through ElevenLabs.

> **Platforms:** macOS, Linux and Windows. macOS is tested by hand; on Linux and Windows the logic is tested in CI, but audio playback has not been checked on real machines yet. Reports are welcome.

## What it does

- `/persona <name>` sets the tone of Claude's replies. Four personas are built in: `tsundere`, `warrior`, `butler`, `noir`. Code, commands and commit messages are not affected.
- Claude adds a short line in `<speak>...</speak>` before tool calls and at the end of each turn. Only that line is sent to the TTS service, never code, file paths or logs.
- Sending a new message stops whatever is being spoken.
- Permission prompts and idle waits are announced out loud.
- If ElevenLabs is unavailable (no key, no credits, no network), the operating system's own voice is used instead.
- Synthesized lines are cached on disk, so a repeated line costs nothing.

The plugin uses only the Python standard library and external audio tools that are already installed (see [Requirements](#requirements)).

## Requirements

- Python 3.10 or newer, available as `python3`, `python` or `py`
- Claude Code
- An [ElevenLabs](https://elevenlabs.io) API key and a voice ID (optional: without them the system voice is used)

| | Audio playback | System voice |
|---|---|---|
| macOS | `afplay` (built in) | `say` (built in) |
| Linux | `mpv` or `ffplay` | `espeak-ng` |
| Windows | PowerShell (built in), or `ffplay` if installed | Windows speech (built in) |

On Windows, Claude Code has to run hooks through Git Bash. If hooks do not run, set `CLAUDE_CODE_GIT_BASH_PATH` to your `bash.exe`, for example `C:\Program Files\Git\bin\bash.exe`.

Music ducking (`duck_music`) works only with the macOS Music app.

## Installation

```sh
git clone https://github.com/Dragonav4/Claude-Code-Voice.git
claude plugin marketplace add "$PWD/Claude-Code-Voice"
claude plugin install voice-personas@claude-code-voice
```

Provide the ElevenLabs credentials either as environment variables:

```sh
export ELEVENLABS_API_KEY="..."
export ELEVENLABS_VOICE_ID="..."
```

or in `~/.claude/voice-personas/config.json` (run `chmod 600` on it). The config file is the safer choice if Claude Code is started from tmux or an IDE that may not see your shell profile.

Restart Claude Code, then run:

```
/persona warrior
/voice test
```

## Commands

| Command | Description |
|---|---|
| `/persona list` | List the available personas |
| `/persona <name>` | Use a persona, starting from the next message |
| `/persona off` | Turn the persona off |
| `/voice on`, `/voice off` | Turn speech on or off |
| `/voice stop` | Stop the current speech |
| `/voice test [text]` | Speak a test line |
| `/voice status` | Show the key, voice, settings and log location |

## Configuration

All fields of `~/.claude/voice-personas/config.json` are optional:

```json
{
  "api_key": "...",
  "default_voice": "VOICE_ID",
  "voices": { "tsundere": "VOICE_ID_1", "warrior": "VOICE_ID_2" },
  "model_id": "eleven_multilingual_v2",
  "rate": 1.0,
  "volume": 1.0,
  "fallback": "say",
  "fallback_voice": null,
  "interrupt_on_prompt": true,
  "notifications": true,
  "duck_music": false,
  "duck_volume": 20,
  "cache_mb": 50
}
```

| Field | Meaning |
|---|---|
| `voices` | ElevenLabs voice per persona |
| `rate`, `volume` | Speech rate (0.5–2.0) and volume (0–1); out-of-range values are clamped |
| `fallback` | `"say"` to use the system voice when ElevenLabs fails, `"none"` to stay silent |
| `fallback_voice` | System voice name. By default a voice matching the line's language is picked (macOS: `say -v '?'` lists voices; Linux: an espeak-ng voice such as `ru`; Windows: a voice name from Settings → Speech) |
| `interrupt_on_prompt` | Stop speaking when you send a new message |
| `notifications` | Announce permission prompts and idle waits |
| `duck_music`, `duck_volume` | Lower the Music app volume while speaking (macOS only) |
| `cache_mb` | Size limit of the phrase cache |

The voice for a persona is chosen in this order: `voices.<persona>`, the `voice_id` in the persona file, `ELEVENLABS_VOICE_ID`, `default_voice`. Environment variables take precedence over the config file.

## Custom personas

Create `~/.claude/voice-personas/personas/<name>.md` using the same format as the files in [`personas/`](personas). A file with the same name as a built-in persona replaces it. Optional frontmatter fields:

```yaml
---
description: One-line description shown in /persona list
voice_id: ELEVENLABS_VOICE_ID
say_permission: Phrase spoken when Claude asks for permission
say_idle: Phrase spoken when Claude is waiting for you
---
```

## How it works

1. On every prompt, a `UserPromptSubmit` hook adds the persona and the `<speak>` rule to Claude's context.
2. After each tool call and at the end of the turn, the `PostToolUse` and `Stop` hooks read the session transcript and collect `<speak>` lines that have not been spoken yet.
3. A background worker synthesizes each line and plays it. Lines play one at a time and never block Claude.
4. A new prompt stops the worker.

Design decisions are recorded in [`docs/adr`](docs/adr).

## Troubleshooting

- Run `/voice status` to check whether the key and voice ID are found.
- Errors are logged to `~/.claude/voice-personas/speak.log` (for example, a missing audio player).
- Set `VOICE_PERSONAS_DRY_RUN=1` to print lines instead of speaking them.

## Limitations

- The `<speak>` tags appear in the reply text.
- If Claude does not write a `<speak>` line, nothing is spoken.
- Each spoken line is a separate ElevenLabs request. The cache only helps with repeated lines.

## Contributing

See [CONVENTIONS.md](CONVENTIONS.md) for the code layout, git flow and tasks. Run `task lint && task test` before opening a pull request.

## Acknowledgements

Some ideas come from other Claude Code TTS projects: interruption and ducking from [ktaletsk/claude-code-tts](https://github.com/ktaletsk/claude-code-tts), the fallback voice and notifications from [ZeldOcarina/claude-code-voice-notifications](https://github.com/ZeldOcarina/claude-code-voice-notifications), and the rate setting from [cc-vox](https://github.com/BestSithInEU/cc-vox). No code was copied.

## License

[Apache 2.0](LICENSE)
