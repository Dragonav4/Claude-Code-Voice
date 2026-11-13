# 3. domain / app / infra layers and a composition root

Date: 2026-11-13

## Status

Accepted

## Context

The first version was a single `speak_hook.py` script that mixed transcript reading, synthesis, playback and state, and computed the home folder globally at import time. Tests had to patch `os.environ` to redirect files.

## Decision

Three layers plus thin entry points:

- `domain` -- pure logic with no IO: settings, state, persona, line selection.
- `app` -- use cases. They get dependencies through a frozen `App` object and never import `infra`.
- `infra` -- disk, network, processes, audio.
- `app/container.py` (plus `app/runner.py`) -- the composition root, the only place where `app` is wired to `infra`.
- `bin/*.py` -- hook entry points, about 10 lines each.

We do not adopt full Clean Architecture with separate DTOs and an interface per adapter. Ports (`typing.Protocol`) appear only where there are several implementations (TTS engines).

## Consequences

- `domain` logic is tested without mocks; `app` use cases are tested by replacing `App` fields.
- The home folder is passed explicitly, so tests do not need the global `os.environ`.
- There are more files, but each is small and does one thing.
