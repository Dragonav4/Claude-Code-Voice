"""<speak>...</speak> lines: finding, cleaning, picking the ones not spoken yet."""

import re
from dataclasses import dataclass

SPEAK_RE = re.compile(r"<speak>(.*?)</speak>", re.S | re.I)
URL_RE = re.compile(r"https?://\S+")
MARKUP_RE = re.compile(r"[`*_#>~|\[\]{}<>]")
SPACES_RE = re.compile(r"\s+")

MAX_SPOKEN_CHARS = 400  # max length of one spoken line
MAX_LINES_PER_RUN = 3  # never build a long speech queue
MAX_SEEN_KEYS = 1000  # how many spoken-line keys to remember


@dataclass(frozen=True)
class TextBlock:
    key: str  # stable block address in the transcript, e.g. "12:0"
    text: str


@dataclass(frozen=True)
class Selection:
    to_say: tuple  # cleaned lines to speak
    seen: tuple  # updated list of spoken keys


def find_speak_lines(blocks):
    """[(key, raw text)] for every <speak> in every block."""
    return [
        (f"{block.key}:{index}", match.group(1))
        for block in blocks
        for index, match in enumerate(SPEAK_RE.finditer(block.text))
    ]


def clean_spoken(text):
    text = URL_RE.sub("", text)
    text = MARKUP_RE.sub("", text)
    return SPACES_RE.sub(" ", text).strip()[:MAX_SPOKEN_CHARS]


def select_new(lines, seen, limit=MAX_LINES_PER_RUN):
    """All new lines are marked as spoken, but only the last `limit` are said."""
    known = set(seen)
    fresh = [(key, text) for key, text in lines if key not in known]
    cleaned = (clean_spoken(text) for _, text in fresh[-limit:])
    return Selection(
        to_say=tuple(text for text in cleaned if len(text) >= 2),
        seen=(tuple(seen) + tuple(key for key, _ in fresh))[-MAX_SEEN_KEYS:],
    )
