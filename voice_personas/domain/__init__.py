"""Чистая логика плагина: без файлов, сети и процессов."""
from .notification import classify_notification
from .persona import DEFAULT_PHRASES, Persona
from .settings import Settings
from .speech import Selection, TextBlock, clean_spoken, find_speak_lines, select_new
from .state import State

__all__ = [
    "DEFAULT_PHRASES",
    "Persona",
    "Selection",
    "Settings",
    "State",
    "TextBlock",
    "classify_notification",
    "clean_spoken",
    "find_speak_lines",
    "select_new",
]
