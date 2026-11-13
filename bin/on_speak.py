#!/usr/bin/env python3
"""Hook PostToolUse и Stop: озвучить новые реплики <speak>."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.narrate import narrate  # noqa: E402
from voice_personas.app.runner import run_hook  # noqa: E402

sys.exit(run_hook(narrate))
