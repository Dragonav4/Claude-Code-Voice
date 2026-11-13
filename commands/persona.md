---
description: Выбрать персону Claude (цундере, воин, ...) или показать список
argument-hint: [имя | list | off]
---
Run exactly this command with the Bash tool and show its output to the user unchanged. Add nothing else.

```
sh "${CLAUDE_PLUGIN_ROOT}/bin/run.sh" "${CLAUDE_PLUGIN_ROOT}/bin/ctl.py" persona "$ARGUMENTS"
```
