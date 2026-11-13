---
description: "Озвучка — on | off | status | stop (оборвать речь) | test [текст] | mode all|end"
argument-hint: "[on | off | status | stop | test [текст] | mode all|end]"
---
Run exactly this command with the Bash tool and show its output to the user unchanged. Add nothing else.

```
sh "${CLAUDE_PLUGIN_ROOT}/bin/run.sh" "${CLAUDE_PLUGIN_ROOT}/bin/ctl.py" voice "$ARGUMENTS"
```
