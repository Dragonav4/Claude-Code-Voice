# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Repository conventions, ADRs, Taskfile, CI and issue/PR templates (#1).
- Secret scanning in CI (gitleaks) and `.gitignore` rules for local state (#5).
- Linux and Windows support: platform layer for locks, processes, players and system voices; `bin/run.sh` picks a working Python; CI on ubuntu, windows and macos (#4).
- Settings from `.env` files in `~/.claude/voice-personas/` and the plugin folder, with `.env.example` listing every variable (#8).

### Changed

- The system voice is picked by the language of the line instead of always using Milena (#4).

### Fixed

- CI ran the tests on the runner's own Python instead of the matrix version (#4).
- A mention of the speak tag earlier in a reply made the whole reply spoken; code is now ignored, the nearest opening tag is used and over-long lines are dropped (#10).

## [0.3.0] - 2026-11-13

### Added

- `domain` / `app` / `infra` layers, thin `bin/` entry points.
- A new prompt cuts off unfinished speech; `/voice stop`.
- Voiced permission and idle notifications with per-persona phrases.
- On-disk phrase cache, macOS `say` fallback, rate, volume and Music.app ducking.
- `/voice test` and an extended `/voice status`.

## [0.1.0] - 2026-11-08

### Added

- Personas (tsundere, warrior, butler, noir) and ElevenLabs narration of `<speak>` lines.
