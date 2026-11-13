"""User choice: the active persona and whether narration is on."""

from dataclasses import dataclass, replace

NARRATION_MODES = ("all", "end")  # every step, or only the end of a turn


@dataclass(frozen=True)
class State:
    persona: str | None = None
    voice: bool = True
    narration: str = "all"

    @classmethod
    def from_dict(cls, data):
        persona = data.get("persona")
        voice = data.get("voice")
        narration = data.get("narration")
        return cls(
            persona=persona if isinstance(persona, str) and persona else None,
            voice=voice if isinstance(voice, bool) else True,
            narration=narration if narration in NARRATION_MODES else "all",
        )

    def to_dict(self):
        return {"persona": self.persona, "voice": self.voice, "narration": self.narration}

    @property
    def speaking(self):
        """Narration works only when a persona is selected."""
        return self.persona is not None and self.voice

    def with_persona(self, name):
        return replace(self, persona=name)

    def with_voice(self, enabled):
        return replace(self, voice=enabled)

    def with_narration(self, mode):
        return replace(self, narration=mode if mode in NARRATION_MODES else self.narration)
