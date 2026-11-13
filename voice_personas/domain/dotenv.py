"""Parsing .env files: KEY=value lines, optional `export`, quotes and comments."""

import re
from types import MappingProxyType

LINE_RE = re.compile(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$")
INLINE_COMMENT_RE = re.compile(r"\s+#.*$")  # only after whitespace, so URLs with # survive


def _value(raw):
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return INLINE_COMMENT_RE.sub("", raw)


def parse_dotenv(text):
    """{NAME: value} for every assignment with a non-empty value. Other lines are ignored."""
    values = {}
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if not match:
            continue
        raw = match.group(2)
        quoted = re.match(r"^(\"[^\"]*\"|'[^']*')", raw)
        value = _value(quoted.group(1) if quoted else raw)
        if value:
            values[match.group(1)] = value
    return MappingProxyType(values)
