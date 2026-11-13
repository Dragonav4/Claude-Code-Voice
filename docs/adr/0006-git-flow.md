# 6. Git flow: main + dev, GitHub Issues, squash into dev

Date: 2026-11-13

## Status

Superseded by [7. Public repository with enforced rulesets](0007-public-repository-with-enforced-rulesets.md)

## Context

We need a simple, predictable process modelled on the Jobbless team project, but without Jira. The repository is private on the free plan, so branch protection settings are not enforced.

## Decision

- `dev` is the default branch and the target of every PR. `main` holds releases only, tagged `vX.Y.Z`.
- Tickets are GitHub Issues. Branch `type/<N>-description`, commit `type(scope): description #N`.
- Squash merge into `dev`; `dev → main` is a merge commit.
- CI runs on every PR: ruff and tests on ubuntu. The macOS job runs only on PRs into `main`, because macOS minutes in a private repo count with a 10x multiplier.

## Consequences

- `dev` history reads as a list of features: one commit per PR.
- The ban on direct pushes to `dev`/`main` is an agreement, not an enforced setting.
- Issue numbers link commits to tasks, and `Closes #N` closes the issue on merge.
