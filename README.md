# Claude-Code-Voice

A Claude Code plugin (macOS): reply personas (tsundere, warrior, butler, noir) that narrate what Claude is doing while it works, voiced through ElevenLabs.

## Features

- **Personas.** `/persona <name>` changes the tone of replies. Code, commands and commits stay neutral.
- **Narration while working.** Before tool calls and at the end of a turn Claude writes a short line in `<speak>...</speak>`, and the plugin voices it. Code, paths and logs never leave the machine.
- **Interruption.** A new message immediately cuts off unfinished speech and the queue. Manually: `/voice stop`.
- **Fallback voice.** With no key, no credits or no network, the system `say` speaks instead (Russian Milena by default).
- **Voiced notifications.** "Need your permission" and "waiting for you" are spoken in the persona's style.
- **Phrase cache.** Repeated lines are not synthesized again and cost no credits.
- **Rate, volume and Music.app ducking** while speaking (off by default).

No dependencies: only `python3` and the built-in `afplay`, `say` and `osascript`.

## Installation

```
claude plugin marketplace add /path/to/Claude-Code-Voice
claude plugin install voice-personas@claude-code-voice
```

Set the ElevenLabs key in `~/.zshrc` (`export ELEVENLABS_API_KEY="..."`) or in `config.json` (see below; then `chmod 600` it). If Claude Code starts from a stale environment (tmux, an IDE), `config.json` is more reliable.

Then in Claude Code: `/persona list`, `/persona warrior`, `/voice test`.

## Commands

| Command | What it does |
|---|---|
| `/persona list` | list personas |
| `/persona <name>` / `/persona off` | pick / turn off (applies from the next message) |
| `/voice on` / `/voice off` | turn narration on / off |
| `/voice stop` | cut off the current speech |
| `/voice test [text]` | check the voice |
| `/voice status` | key, voice, settings, log path |

## Settings

`~/.claude/voice-personas/config.json`, every field is optional:

```json
{
  "api_key": "...",
  "default_voice": "VOICE_ID",
  "voices": { "tsundere": "VOICE_ID_1", "warrior": "VOICE_ID_2" },
  "model_id": "eleven_multilingual_v2",
  "rate": 1.0,
  "volume": 1.0,
  "fallback": "say",
  "fallback_voice": "Milena",
  "interrupt_on_prompt": true,
  "notifications": true,
  "duck_music": false,
  "duck_volume": 20,
  "cache_mb": 50
}
```

- Voice lookup order: `voices.<persona>`, then `voice_id:` in the persona file, then `ELEVENLABS_VOICE_ID`, then `default_voice`.
- `rate` is 0.5 to 2.0, `volume` is 0 to 1. Out-of-range values are clamped.
- `fallback: "none"` keeps silent when ElevenLabs is unavailable.
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` and `ELEVENLABS_MODEL_ID` from the environment override the config.

## Custom personas

Put a file at `~/.claude/voice-personas/personas/<name>.md` in the same format as the files in `personas/`. It overrides a built-in persona with the same name. The frontmatter may set `voice_id:`, `say_permission:` and `say_idle:` (notification phrases).

## Debugging

- Narration errors go to `~/.claude/voice-personas/speak.log`.
- `VOICE_PERSONAS_DRY_RUN=1` prints lines instead of synthesizing and playing them.

## Development

Conventions, git flow and layers are described in [CONVENTIONS.md](CONVENTIONS.md), decisions in [docs/adr](docs/adr). Common tasks: `task test`, `task lint`, `task validate`, `task reinstall`.

```
bin/                 entry points: hooks and commands (~10 lines each)
voice_personas/
  domain/            pure logic: settings, persona, lines, notifications (no IO)
  app/               use cases: narrate, notify, prompt, speak, control
    container.py     composition root, the only place where app meets infra
  infra/             outside world: files, transcript, ElevenLabs, afplay/say, Music, processes
personas/            built-in personas
```

The path of one line: `bin/on_speak.py` → `app/narrate.py` (new `<speak>` lines from the transcript) → queue → `bin/worker.py` → `app/speak.py` (ElevenLabs or `say`) → `infra/audio.py`.

## Known limitations

- `<speak>` tags are visible in the reply text.
- If Claude does not write `<speak>`, nothing is spoken. This depends on how well the model follows the prompt.
- Every line is a separate paid ElevenLabs request. The cache helps only with repeated phrases.

## Credits

Interruption and ducking were inspired by [ktaletsk/claude-code-tts](https://github.com/ktaletsk/claude-code-tts), the fallback voice and notifications by [ZeldOcarina/claude-code-voice-notifications](https://github.com/ZeldOcarina/claude-code-voice-notifications), speech rate by [cc-vox](https://github.com/BestSithInEU/cc-vox). The code is written from scratch.
