# Claude-Code-Voice — Project Context

## Project

A Claude Code plugin, `voice-personas`: personas change the tone of replies, and short `<speak>` lines are voiced while Claude works.
Read @CONVENTIONS.md for project conventions and `docs/adr/` for architecture decisions.

## How to Work

- Before editing, identify the layer (`domain` / `app` / `infra`) and follow the import rules in `CONVENTIONS.md`.
- Standard library only. A new external dependency is a decision for an ADR and for the user, not for the agent.
- Failing test first, then code. Before calling anything done: `task lint && task test`.
- Never guess. If an issue or task is unclear, ask.

## Pitfall: hooks run from the repo

The `claude-code-voice` marketplace points at this folder, so the hooks of a live session run **straight from the repo**.
Renaming or deleting a file referenced in `hooks/hooks.json` makes the live session fail on every action until it is restarted.
When moving entry points, delete the old path only after `task reinstall` and a Claude Code restart.

## Git

Branches, commits and PRs follow the Git section of `CONVENTIONS.md`. No AI attribution in commits.
