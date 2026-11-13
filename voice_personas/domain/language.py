"""Language of a spoken line, used to pick a matching system voice."""

import re

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


def detect_language(text):
    """ "ru" for Cyrillic text, None when the system default voice is fine."""
    return "ru" if CYRILLIC_RE.search(text) else None
