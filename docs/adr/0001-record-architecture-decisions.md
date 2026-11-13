# 1. Record architecture decisions

Date: 2026-11-13

## Status

Accepted

## Context

We need to record the architectural, dependency and process decisions made on this project together with their reasons. Otherwise a month later nobody remembers why something was done this way, and it is easy to break it by accident.

## Decision

We will use Architecture Decision Records, as [described by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions), stored as `docs/adr/NNNN-title.md`.

## Consequences

Every notable decision is a separate short file. Replaced decisions stay in history with the status `Superseded by NNNN`. For a lightweight ADR toolset, see Nat Pryce's [adr-tools](https://github.com/npryce/adr-tools) (`.adr-dir` points to `docs/adr`).
