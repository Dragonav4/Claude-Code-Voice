"""Narration settings from config.json and environment variables, validated."""

from dataclasses import dataclass, field
from types import MappingProxyType

FALLBACK_MODES = ("say", "none")


def _text(value):
    return value if isinstance(value, str) and value.strip() else None


def _flag(value, default):
    return value if isinstance(value, bool) else default


def _number(value, default, low, high):
    """A number clamped to [low, high]; garbage and bools give the default."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return default
    try:
        number = float(value)
    except ValueError:
        return default
    return type(default)(min(max(number, low), high))


def _voices(value):
    if not isinstance(value, dict):
        return MappingProxyType({})
    return MappingProxyType(
        {
            name: voice_id
            for name, voice_id in value.items()
            if isinstance(name, str) and _text(voice_id)
        }
    )


@dataclass(frozen=True)
class Settings:
    api_key: str | None = None
    default_voice: str | None = None
    voices: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))
    model_id: str = "eleven_multilingual_v2"
    rate: float = 1.0  # speech rate
    volume: float = 1.0  # afplay volume
    fallback: str = "say"  # "say" for the system voice, "none" for silence
    fallback_voice: str = "Milena"  # `say` voice (Russian on macOS)
    interrupt_on_prompt: bool = True  # a new prompt cuts off speech
    notifications: bool = True  # voice permission / idle notifications
    duck_music: bool = False  # lower Music.app volume while speaking
    duck_volume: int = 20  # Music.app volume while ducked
    cache_mb: int = 50  # phrase cache size

    @classmethod
    def from_sources(cls, config, env):
        """The environment beats config.json for the key, default voice and model."""
        d = cls()
        fallback = config.get("fallback")
        return cls(
            api_key=_text(env.get("ELEVENLABS_API_KEY")) or _text(config.get("api_key")),
            default_voice=(
                _text(env.get("ELEVENLABS_VOICE_ID")) or _text(config.get("default_voice"))
            ),
            voices=_voices(config.get("voices")),
            model_id=(
                _text(env.get("ELEVENLABS_MODEL_ID")) or _text(config.get("model_id")) or d.model_id
            ),
            rate=_number(config.get("rate"), d.rate, 0.5, 2.0),
            volume=_number(config.get("volume"), d.volume, 0.0, 1.0),
            fallback=fallback if fallback in FALLBACK_MODES else d.fallback,
            fallback_voice=_text(config.get("fallback_voice")) or d.fallback_voice,
            interrupt_on_prompt=_flag(config.get("interrupt_on_prompt"), d.interrupt_on_prompt),
            notifications=_flag(config.get("notifications"), d.notifications),
            duck_music=_flag(config.get("duck_music"), d.duck_music),
            duck_volume=_number(config.get("duck_volume"), d.duck_volume, 0, 100),
            cache_mb=_number(config.get("cache_mb"), d.cache_mb, 0, 1000),
        )

    def voice_for(self, persona):
        """voices.<persona> > the persona voice_id > the default voice."""
        if persona is None:
            return self.default_voice
        return self.voices.get(persona.name) or persona.voice_id or self.default_voice
