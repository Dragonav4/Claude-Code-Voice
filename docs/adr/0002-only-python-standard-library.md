# 2. Python standard library only

Date: 2026-11-13

## Status

Accepted

## Context

Hooks run on the user's system `python3` on every Claude Code action. The plugin has no virtual environment, and `pip install` into the global Python breaks other environments and adds a separate install step.

## Decision

Plugin code uses only the Python 3.10+ standard library. Heavy work (speech synthesis, playback) is done by external programs that the plugin runs as processes: `afplay`, `say`, `piper`, `espeak-ng`. Network calls go through `urllib`.

## Consequences

- Installing the plugin is one command with no dependencies.
- Every external program is optional: if it is missing, the plugin moves to the next option or stays silent and logs the reason.
- No vendor SDKs (ElevenLabs etc.); HTTP is written by hand, which is a few lines at our scale.
- Development tools (`ruff`) never reach the runtime and are run through `uvx`.
