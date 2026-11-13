#!/usr/bin/env python3
"""Hook UserPromptSubmit: оборвать речь и добавить персону в контекст."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.prompt import on_prompt  # noqa: E402
from voice_personas.app.runner import run_hook  # noqa: E402

sys.exit(run_hook(on_prompt))
