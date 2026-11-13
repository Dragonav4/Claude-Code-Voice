# Project Conventions

## Repository Structure

- `.claude-plugin/` -- plugin manifest (`plugin.json`) and a marketplace served from this folder (`marketplace.json`).
- `.github/` -- CI, dependabot, PR and issue templates.
- `bin/` -- entry points: hooks, the `ctl.py` command and `run.sh`, which picks a working Python. Wiring only, no logic.
- `commands/` -- the `/persona` and `/voice` slash commands.
- `docs/adr/` -- architecture decision records.
- `hooks/hooks.json` -- which hooks Claude Code calls and which `bin/*.py` handles each one.
- `personas/` -- built-in personas.
- `tests/` -- `unittest` test suite.
- `voice_personas/` -- plugin code, see [Layers](#layers).
- `Taskfile.yaml` -- common operations, see [Tasks](#tasks).
- `AGENT.md` / `CLAUDE.md` -- context for AI agents. `CONVENTIONS.md` -- this file.

## Layers

```
bin → app → domain
       ↓
     infra   (wired only in app/container.py and app/runner.py)
```

- `domain/` -- pure logic: no files, network, processes or `os.environ`. Tested without mocks.
- `app/` -- use cases (`narrate`, `notify`, `prompt`, `speak`, `control`). They get dependencies only through the `App` object and never import `infra`.
- `app/container.py` and `app/runner.py` -- the composition root, the only place where `app` meets a concrete `infra`.
- `infra/` -- the outside world: disk, transcript, ElevenLabs, players, Music.app, processes.
- `infra/platform/` -- the only place that knows about macOS, Linux and Windows differences ([ADR 0008](docs/adr/0008-cross-platform-support.md)).

Boundary check: `rg "infra" voice_personas/app --glob '!container.py' --glob '!runner.py'` must find nothing.

## Code

- Python 3.10+ standard library only. External programs (`afplay`, `say`, `espeak-ng`, PowerShell) run as processes ([ADR 0002](docs/adr/0002-only-python-standard-library.md)).
- Code must run on macOS, Linux and Windows. OS checks belong in `infra/platform/`; never import `fcntl`, call `os.killpg` or assume `python3` elsewhere.
- Model-written text and file paths reach external programs only through argv lists, stdin or environment variables, never inside a shell or PowerShell script string.
- Data is immutable: `@dataclass(frozen=True)`, dicts wrapped in `MappingProxyType`. Changes go through `replace()` / `with_*()` and return a new object.
- Files under 200 lines, functions under 50. Magic numbers become named constants at the top of the module.
- Hooks never crash Claude Code: errors go to `speak.log`, the exit code is always 0.
- Everything coming from outside (stdin JSON, `config.json`, the transcript) is validated at the boundary. Garbage falls back to defaults.
- Code, comments and docs are in English. User-facing strings (command output, spoken phrases, persona files) stay in Russian.
- Style is enforced by `ruff` (config in `pyproject.toml`).

## Tests

- New logic and bug fixes start with a failing test.
- `domain` is tested without mocks; `infra` and `app` use `tests/support.TempHomeTest`, which gives each test an empty temporary `~/.claude/voice-personas` through `env`, without touching the global `os.environ`.
- `bin/*.py` entry points are tested as separate processes, the way Claude Code runs them.

## Git

Tickets are GitHub Issues. Work without an issue is acceptable only for a hotfix.

Branch format: `type/<issue number>-short-description`, e.g. `feat/2-piper-tts`.
Commit format: `type(scope if needed): description #<issue number>`, e.g. `feat(tts): add piper engine #2`.
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`.

Branches:
- `dev` -- the default branch, every PR targets it.
- `main` -- releases only: a `dev → main` PR plus a `vX.Y.Z` tag.

`dev` and `main` are protected by rulesets ([ADR 0007](docs/adr/0007-public-repository-with-enforced-rulesets.md)): no direct pushes, no force pushes, no deletion, and a PR merges only with green required checks (`Lint and test`, `Secret scan`) and an up-to-date branch. Release tags `v*` cannot be moved or deleted.

### PRs

- One issue -- one branch -- one PR into `dev`, with `Closes #N` in the description.
- Before review: CI is green and the branch contains the latest `dev` (`git merge dev`).
- PRs into `dev` are squash-merged (the only method the ruleset allows), leaving one commit with `(#PR)` in history.
- Explain non-obvious decisions in a code comment or in the PR. Big ones get an ADR.

### Release

1. Move the `Unreleased` section of `CHANGELOG.md` to a new version and bump `version` in `.claude-plugin/plugin.json`.
2. Open a `dev → main` PR and merge it with a merge commit.
3. Tag `vX.Y.Z` on `main` and run `gh release create`.

## Secrets

- API keys live only in `~/.claude/voice-personas/config.json` or the environment, never in the repository.
- `.gitignore` excludes `config.json`, `.env`, logs and audio files.
- GitHub push protection and the gitleaks CI job catch keys that slip through. A key that reached GitHub must be revoked, even if the PR was never merged.
- Commit with the noreply email: `git config user.email "<id>+<login>@users.noreply.github.com"`.

## ADR

A decision that changes architecture, dependencies or process is recorded in `docs/adr/NNNN-title.md` in the Nygard format: Status, Context, Decision, Consequences. A replaced decision is not deleted; its status becomes `Superseded by NNNN`.

## Tasks

Requires [Task](https://taskfile.dev). List them with `task --list`.

- `test` -- run the whole test suite.
- `lint` -- `ruff check` plus a formatting check.
- `format` -- format the code.
- `validate` -- `claude plugin validate .`.
- `reinstall` -- pull repo changes into the installed plugin. Restart Claude Code afterwards.

## CLI Tools

- `task` -- task runner.
- `uv` -- runs `uvx ruff` and installs `piper-tts`.
- `gh` -- issues, PRs, releases.
- `rg`, `fd` -- search.
