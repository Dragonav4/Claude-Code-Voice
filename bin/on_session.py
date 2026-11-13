#!/usr/bin/env python3
"""SessionStart hook: give Claude the full persona at the start and after /clear or compaction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.prompt import on_session_start  # noqa: E402
from voice_personas.app.runner import run_hook  # noqa: E402

sys.exit(run_hook(on_session_start))
