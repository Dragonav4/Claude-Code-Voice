# 8. Cross-platform support: macOS, Linux, Windows

Date: 2026-11-13

## Status

Accepted

## Context

The plugin was written for macOS: `fcntl` locks, POSIX process groups, `ps`, `afplay`, `say` and `python3` in `hooks.json`. On Windows it failed at import time (`fcntl` does not exist), and Claude Code runs hooks through Git Bash there, where `python3` is often a Microsoft Store stub that exits with code 49.

## Decision

- Everything that depends on the OS lives in `infra/platform/`:
  - `locks` -- `fcntl.flock` on macOS/Linux, `msvcrt.locking` on Windows, both polled with a timeout.
  - `processes` -- a detached worker in its own process group (`start_new_session` / `CREATE_NEW_PROCESS_GROUP`), stopped with `killpg` or `taskkill /T`, identified by its command line (`ps` / `Get-CimInstance`).
  - `players` -- `afplay` on macOS; `mpv` or `ffplay` anywhere; `paplay`/`aplay` for wav on Linux; PowerShell `MediaPlayer` on Windows.
  - `voices` -- `say` on macOS, `espeak-ng` on Linux, PowerShell `System.Speech` on Windows.
- Hooks and commands call `sh bin/run.sh <script>`. The launcher tries `python3`, `python` and `py` and uses the first one that is really Python 3.10+.
- Text and file paths reach PowerShell and espeak only through stdin and environment variables, never inside a script string.
- The system voice is picked by the language of the line (an installed Russian voice for Cyrillic text) unless `fallback_voice` is set.
- stdin/stdout are switched to UTF-8 in every entry point, because Windows pipes default to the ANSI code page.
- Music ducking stays macOS-only.
- CI runs the tests and a launcher smoke test on ubuntu, windows and macos, all in bash.

## Consequences

- One code path per OS, chosen once in `app/container.py`; the rest of the code does not know which OS it runs on.
- Windows needs Git Bash (Claude Code needs it too); without it hooks fall back to `cmd.exe`, which has no `sh`.
- Linux needs `mpv` or `ffplay` for mp3 and `espeak-ng` for the system voice.
- CI verifies the logic on every OS but cannot hear audio: real playback on Linux and Windows has to be checked by hand.
