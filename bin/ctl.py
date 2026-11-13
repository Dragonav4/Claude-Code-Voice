#!/usr/bin/env python3
"""/persona and /voice commands.

ctl.py persona [list|<name>|off]
ctl.py voice [on|off|status|stop|test]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.container import build_app  # noqa: E402
from voice_personas.app.control import run_command  # noqa: E402
from voice_personas.app.runner import use_utf8_stdio  # noqa: E402

if __name__ == "__main__":
    use_utf8_stdio()
    code, text = run_command(build_app(), sys.argv[1:])
    print(text)
    sys.exit(code)
