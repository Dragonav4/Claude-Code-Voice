"""Выбор пользователя: активная персона и включена ли озвучка."""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class State:
    persona: str | None = None
    voice: bool = True

    @classmethod
    def from_dict(cls, data):
        persona = data.get("persona")
        voice = data.get("voice")
        return cls(
            persona=persona if isinstance(persona, str) and persona else None,
            voice=voice if isinstance(voice, bool) else True,
        )

    def to_dict(self):
        return {"persona": self.persona, "voice": self.voice}

    @property
    def speaking(self):
        """Озвучка работает только при выбранной персоне."""
        return self.persona is not None and self.voice

    def with_persona(self, name):
        return replace(self, persona=name)

    def with_voice(self, enabled):
        return replace(self, voice=enabled)
