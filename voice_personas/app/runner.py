"""Entry point wiring: parse stdin, build App, send errors to the log, not the screen.

Together with container.py this is the composition root: the log has to work
even if App fails to build.
"""

import json
import os
import sys
import traceback

from ..infra.paths import Paths
from ..infra.storage import Log
from .container import build_app


def read_payload(stream):
    try:
        data = json.load(stream)
    except (ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def log_crash(where):
    Log(Paths.from_env(os.environ).log_file).write(f"{where} failed:\n{traceback.format_exc()}")


def run_hook(handler):
    """A hook never crashes Claude Code: it always exits with code 0."""
    try:
        output = handler(build_app(), read_payload(sys.stdin))
        if output:
            print(output)  # for UserPromptSubmit, stdout goes into Claude's context
    except Exception:
        log_crash(handler.__name__)
    return 0
