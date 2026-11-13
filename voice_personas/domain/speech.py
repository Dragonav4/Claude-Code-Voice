"""<speak>...</speak> lines: finding, cleaning, picking the ones not spoken yet."""

import re
from dataclasses import dataclass

# The nearest opening tag before each closing tag: an earlier stray mention of the
# tag must not swallow the rest of the reply (#10).
SPEAK_RE = re.compile(r"<speak>((?:(?!<speak>).)*?)</speak>", re.S | re.I)
CODE_FENCE_RE = re.compile(r"```.*?(?:```|\Z)", re.S)  # an unclosed fence hides the rest
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
URL_RE = re.compile(r"https?://\S+")
# ElevenLabs v3/v4 read these as performance direction, not as words (#13).
AUDIO_TAGS = ("sarcastic", "mischievously", "laughs", "sighs", "exhales", "whispers")
AUDIO_TAG_RE = re.compile(r"\[(" + "|".join(AUDIO_TAGS) + r")\]", re.I)
BRACKET_TAG_RE = re.compile(r"\[[^\[\]\n]{0,40}\]")  # any other [direction] is dropped whole
TAG_MODEL_PREFIXES = ("eleven_v3", "eleven_v4")
MARKUP_RE = re.compile(r"[`*_#>~|\[\]{}<>]")
SPACES_RE = re.compile(r"\s+")

MAX_SPOKEN_CHARS = 300  # a longer line is not a spoken line, so it is dropped
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


def _without_code(text):
    """Tags inside code are examples, not lines to speak."""
    return INLINE_CODE_RE.sub(" ", CODE_FENCE_RE.sub(" ", text))


def find_speak_lines(blocks):
    """[(key, raw text)] for every real spoken line in every block."""
    return [
        (f"{block.key}:{index}", match.group(1))
        for block in blocks
        for index, match in enumerate(SPEAK_RE.finditer(_without_code(block.text)))
    ]


def is_speakable(raw):
    """A spoken line is one short paragraph; anything else is a parsing accident."""
    return "\n\n" not in raw.strip() and len(clean_spoken(raw)) <= MAX_SPOKEN_CHARS


def clean_spoken(text):
    """Plain speakable text. Known audio tags are kept in lowercase, other tags are removed."""
    tags = []

    def keep(match):
        tags.append(f"[{match.group(1).lower()}]")
        return f"\x00{len(tags) - 1}\x00"

    text = AUDIO_TAG_RE.sub(keep, text)
    text = BRACKET_TAG_RE.sub(" ", text)
    text = URL_RE.sub("", text)
    text = MARKUP_RE.sub("", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: tags[int(m.group(1))], text)
    return SPACES_RE.sub(" ", text).strip()


def strip_audio_tags(text):
    """The line without any audio tags, for engines that would read them aloud."""
    return SPACES_RE.sub(" ", AUDIO_TAG_RE.sub(" ", text)).strip()


def supports_audio_tags(model_id):
    return str(model_id).startswith(TAG_MODEL_PREFIXES)


def select_new(lines, seen, limit=MAX_LINES_PER_RUN):
    """All new lines are marked as spoken, but only the last `limit` are said."""
    known = set(seen)
    fresh = [(key, text) for key, text in lines if key not in known]
    cleaned = (clean_spoken(text) for _, text in fresh[-limit:] if is_speakable(text))
    return Selection(
        to_say=tuple(text for text in cleaned if len(text) >= 2),
        seen=(tuple(seen) + tuple(key for key, _ in fresh))[-MAX_SEEN_KEYS:],
    )
