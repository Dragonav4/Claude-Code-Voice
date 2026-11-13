# 5. TTS engine chain: ElevenLabs → Piper → system voice

Date: 2026-11-13

## Status

Accepted

## Context

ElevenLabs sounds best but costs money and needs a network connection and a key. The system `say` is free but sounds noticeably worse. A local neural TTS has to speak Russian: Kokoro does not support Russian, and Silero pulls in PyTorch, which violates [ADR 0002](0002-only-python-standard-library.md).

## Decision

- A `SpeechEngine.audio_file(text, voice) -> Path | None` port in `app`. Every engine returns a file; `Player` only plays it.
- Implementations in `infra/engines`: ElevenLabs (HTTP), [Piper](https://github.com/OHF-Voice/piper1-gpl) (CLI, offline, has Russian voices), the system voice (`say` on macOS, `espeak-ng` on Linux).
- The order comes from the `engines` setting, by default `elevenlabs → piper → system`. Each line uses the first engine that returns a file.
- One shared file cache for all engines.

## Consequences

- Without a key or network the plugin speaks through Piper if it is installed, otherwise through the system voice.
- Piper and a voice model are installed separately (`uv tool install piper-tts`). The plugin does not download them.
- A new engine is one class in `infra/engines` and one line in `app/container.py`.
