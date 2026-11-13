# 4. Narrate <speak> lines through hooks

Date: 2026-11-13

## Status

Accepted

## Context

Similar plugins (cc-vox, claude-code-tts) read a summary of the reply after it ends. We want the persona to speak while it works: what it is doing now and how it ended. Code, paths and logs must not reach the TTS or a third-party API.

## Decision

- The `UserPromptSubmit` hook adds a rule to the context: before tool calls and at the end of a turn, write a short line inside `<speak>...</speak>`.
- The `PostToolUse` and `Stop` hooks read the session transcript, find tags that have not been spoken yet and hand them to a background worker.
- Only the tag content is spoken, after stripping markup and URLs.
- A new user prompt cuts off unfinished speech.

## Consequences

- Only phrases the model explicitly wrote for speech leave the machine.
- The tags are visible in the reply text in the terminal.
- Narration depends on the model following the rule. No tag means silence.
- Every line is a separate TTS request. That costs money, hence the cache, limits and a quiet mode.
