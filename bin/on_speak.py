#!/usr/bin/env python3
"""PostToolUse and Stop hook: speak new <speak> lines."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.narrate import narrate  # noqa: E402
from voice_personas.app.runner import run_hook  # noqa: E402

sys.exit(run_hook(narrate))
