"""Persona: reply tone, voice and notification phrases."""

import hashlib
import re
from dataclasses import dataclass, field
from types import MappingProxyType

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)

DEFAULT_PHRASES = MappingProxyType(
    {
        "permission": "Нужно твоё разрешение.",
        "idle": "Я закончил и жду тебя.",
    }
)

SPEAK_RULES = """\
Voice narration (the user hears these lines through text-to-speech):
- Before a batch of tool calls, and at the very end of every turn, include one short spoken line wrapped in <speak>...</speak> tags, written in the persona's voice.
- A spoken line is plain sentences only: at most ~25 words, in the same language as the user's latest message, with no code, file paths, URLs, markdown or emoji. Say what you are about to do, or what the outcome is.
- Put nothing inside <speak> that is not meant to be read aloud.
- Never write the tag itself anywhere else, not even inside code or when explaining how narration works: a stray opening tag makes the rest of the reply spoken. In prose, call it "the speak tag".
- Keep the normal written answer complete. The spoken line is an addition, not a replacement."""


def _parse_frontmatter(text):
    """(meta, body). meta holds plain `key: value` lines."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, match.group(2).strip()


@dataclass(frozen=True)
class Persona:
    name: str
    description: str = ""
    prompt: str = ""
    voice_id: str | None = None
    phrases: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))

    @classmethod
    def parse(cls, name, text):
        meta, body = _parse_frontmatter(text)
        phrases = {kind: meta[f"say_{kind}"] for kind in DEFAULT_PHRASES if meta.get(f"say_{kind}")}
        return cls(
            name=name,
            description=meta.get("description", ""),
            prompt=body,
            voice_id=meta.get("voice_id") or None,
            phrases=MappingProxyType(phrases),
        )

    def phrase(self, kind):
        return self.phrases.get(kind) or DEFAULT_PHRASES[kind]

    def context(self, with_voice):
        """The full persona text: sent once per session and after every change."""
        parts = [f"[voice-personas] Active persona: {self.name}", self.prompt]
        if with_voice:
            parts.append(SPEAK_RULES)
        return "\n\n".join(parts)

    def reminder(self, with_voice):
        """One line for the following prompts: the full text is already in the history."""
        line = (
            f"[voice-personas] Persona {self.name} is still active: "
            "follow its rules from earlier in this conversation."
        )
        return line + (" Keep narrating with the speak tag as instructed." if with_voice else "")

    def fingerprint(self, with_voice):
        """Changes whenever the full text would change: persona, voice or file edits."""
        return hashlib.sha256(self.context(with_voice).encode("utf-8")).hexdigest()[:16]
