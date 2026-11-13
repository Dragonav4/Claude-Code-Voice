# 7. Public repository with enforced rulesets

Date: 2026-11-13

## Status

Accepted

Supersedes [6. Git flow: main + dev, GitHub Issues, squash into dev](0006-git-flow.md)

## Context

The plugin is meant to be used by other people, so the repository has to be public. A public repository also gets branch rulesets and secret scanning for free, which a private repository on the free plan does not.

Before going public, the history was rewritten to replace a personal email address in commit metadata with the GitHub noreply address. GitHub keeps the commits of every pull request forever, so the history was pushed into a fresh repository; the original one is kept private as `Claude-Code-Voice-archive`.

## Decision

- `dev` is the default branch and the target of every PR. `main` holds releases only, tagged `vX.Y.Z`.
- Tickets are GitHub Issues. Branch `type/<N>-description`, commit `type(scope): description #N`.
- Rulesets on `dev` and `main`, with no bypass actors: no deletion, no force push, changes only through a PR with green required checks, and the branch must be up to date with its base.
- `dev` accepts only squash merges, `main` only merge commits. Rebase merging is disabled.
- A ruleset on `v*` tags forbids deleting or moving a release tag.
- GitHub secret scanning with push protection is on. CI also runs gitleaks on every PR, and that check is required.
- CI runs on ubuntu only. Windows and macOS jobs are added together with platform support (#4).
- Commits use the noreply email (`git config user.email` in the repository), and the account keeps its email private.

## Consequences

- Nobody, including the owner, can rewrite or delete `dev`, `main` or a release tag. Undoing a change means a new commit.
- A pushed key is blocked by push protection when GitHub knows its format, and caught by gitleaks in the PR otherwise. A key that reached GitHub still has to be revoked.
- macOS-specific code is covered only by mocked tests until #4.
