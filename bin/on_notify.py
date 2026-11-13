#!/usr/bin/env python3
"""Hook Notification: голосом сказать, что Claude ждёт разрешения или ввода."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.notify import notify  # noqa: E402
from voice_personas.app.runner import run_hook  # noqa: E402

sys.exit(run_hook(notify))
