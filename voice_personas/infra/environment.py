"""The effective environment: process variables plus optional .env files.

Precedence: the real environment > ~/.claude/voice-personas/.env > <plugin>/.env.
"""

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from ..domain import parse_dotenv
from .paths import default_home

DOTENV = ".env"
HOME_VARIABLE = "VOICE_PERSONAS_HOME"


@dataclass(frozen=True)
class LoadedEnvironment:
    env: MappingProxyType
    warnings: tuple


def _read(path):
    """(values, warning or None). A missing or unreadable file gives no values."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}, None
    warning = None
    if os.name != "nt" and path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        warning = f"{path} is readable by other users; run: chmod 600 {path}"
    return dict(parse_dotenv(text)), warning


def _home(env):
    value = env.get(HOME_VARIABLE)
    return Path(os.path.expanduser(value)) if value else default_home()


def load_environment(base_env, env_dir):
    """Merges `base_env` (usually os.environ) with the .env files, without changing it."""
    plugin_values, plugin_warning = _read(Path(env_dir) / DOTENV)
    home = _home({**plugin_values, **base_env})
    home_values, home_warning = _read(home / DOTENV)
    merged = {**plugin_values, **home_values, **base_env}
    if merged.get(HOME_VARIABLE):
        merged[HOME_VARIABLE] = str(_home(merged))
    warnings = tuple(w for w in (plugin_warning, home_warning) if w)
    return LoadedEnvironment(env=MappingProxyType(merged), warnings=warnings)
