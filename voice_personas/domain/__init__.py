"""Pure plugin logic: no files, network or processes."""

from .dotenv import parse_dotenv
from .language import detect_language
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
    "detect_language",
    "clean_spoken",
    "find_speak_lines",
    "parse_dotenv",
    "select_new",
]
