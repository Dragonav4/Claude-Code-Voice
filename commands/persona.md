---
description: Pick a persona for Claude (tsundere, warrior, ...) or list them
argument-hint: [name | list | on | off]
---
Run exactly this command with the Bash tool and show its output to the user unchanged. Add nothing else.

```
sh "${CLAUDE_PLUGIN_ROOT}/bin/run.sh" "${CLAUDE_PLUGIN_ROOT}/bin/ctl.py" persona "$ARGUMENTS"
```
