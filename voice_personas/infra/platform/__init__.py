"""Operating-system differences in one place: macOS, Linux and Windows."""

import sys
from dataclasses import dataclass, field
from types import MappingProxyType

MACOS = "macos"
LINUX = "linux"
WINDOWS = "windows"


def current_system(platform=sys.platform):
    if platform == "darwin":
        return MACOS
    if platform.startswith("win"):
        return WINDOWS
    return LINUX  # Linux and other Unix-likes share the same tools


@dataclass(frozen=True)
class Command:
    """An external program to run: argv, optional stdin text and extra environment."""

    argv: tuple
    stdin: str | None = None
    env: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))
