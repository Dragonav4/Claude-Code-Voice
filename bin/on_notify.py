#!/usr/bin/env python3
"""Notification hook: say out loud that Claude waits for permission or input."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.notify import notify  # noqa: E402
from voice_personas.app.runner import run_hook  # noqa: E402

sys.exit(run_hook(notify))
