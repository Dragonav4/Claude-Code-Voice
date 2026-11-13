"""Ducking: lowers Music.app volume while a line is playing."""

import contextlib
import shutil
import subprocess

OSASCRIPT_TIMEOUT_S = 3
GET_VOLUME = (
    'if application "Music" is running then tell application "Music" to return sound volume'
)
SET_VOLUME = 'tell application "Music" to set sound volume to {level}'


def _osascript(script):
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=OSASCRIPT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def music_volume():
    """Music.app volume, or None if it is not running. Never launches Music."""
    value = _osascript(GET_VOLUME)
    return int(value) if value and value.isdigit() else None


def set_music_volume(level):
    _osascript(SET_VOLUME.format(level=int(level)))


@contextlib.contextmanager
def ducked(enabled, level):
    """Ducks for the block and always restores the volume, even on error."""
    original = music_volume() if enabled and shutil.which("osascript") else None
    if original is None or original <= level:
        yield
        return
    set_music_volume(level)
    try:
        yield
    finally:
        set_music_volume(original)
