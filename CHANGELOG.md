# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Repository conventions, ADRs, Taskfile, CI and issue/PR templates (#1).

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
