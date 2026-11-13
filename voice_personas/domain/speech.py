"""Реплики <speak>...</speak>: поиск, очистка, выбор ещё не озвученных."""
import re
from dataclasses import dataclass

SPEAK_RE = re.compile(r"<speak>(.*?)</speak>", re.S | re.I)
URL_RE = re.compile(r"https?://\S+")
MARKUP_RE = re.compile(r"[`*_#>~|\[\]{}<>]")
SPACES_RE = re.compile(r"\s+")

MAX_SPOKEN_CHARS = 400   # длина одной реплики
MAX_LINES_PER_RUN = 3    # не копим длинную очередь озвучки
MAX_SEEN_KEYS = 1000     # сколько ключей озвученных реплик помнить


@dataclass(frozen=True)
class TextBlock:
    key: str   # стабильный адрес блока в транскрипте, например "12:0"
    text: str


@dataclass(frozen=True)
class Selection:
    to_say: tuple   # очищенные реплики для озвучки
    seen: tuple     # обновлённый список озвученных ключей


def find_speak_lines(blocks):
    """[(ключ, сырой текст)] для всех <speak> во всех блоках."""
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
    """Новые реплики помечаются озвученными все, но говорятся только последние `limit`."""
    known = set(seen)
    fresh = [(key, text) for key, text in lines if key not in known]
    cleaned = (clean_spoken(text) for _, text in fresh[-limit:])
    return Selection(
        to_say=tuple(text for text in cleaned if len(text) >= 2),
        seen=(tuple(seen) + tuple(key for key, _ in fresh))[-MAX_SEEN_KEYS:],
    )
