import unittest

import support  # noqa: F401
from voice_personas.domain import (
    Persona, Settings, State, TextBlock, classify_notification, clean_spoken,
    find_speak_lines, select_new,
)
from voice_personas.domain.speech import MAX_SPOKEN_CHARS


class SettingsTest(unittest.TestCase):
    def test_defaults(self):
        s = Settings.from_sources({}, {})
        self.assertEqual((s.rate, s.fallback, s.fallback_voice), (1.0, "say", "Milena"))
        self.assertTrue(s.interrupt_on_prompt)
        self.assertIsNone(s.api_key)

    def test_numbers_clamped_and_typed(self):
        s = Settings.from_sources({"rate": 9, "volume": -1, "duck_volume": 500.7}, {})
        self.assertEqual((s.rate, s.volume, s.duck_volume), (2.0, 0.0, 100))
        self.assertIsInstance(s.duck_volume, int)

    def test_garbage_gives_defaults(self):
        s = Settings.from_sources({"rate": "fast", "notifications": "yes", "fallback": "x",
                                   "cache_mb": True, "voices": ["bad"]}, {})
        self.assertEqual((s.rate, s.notifications, s.fallback, s.cache_mb), (1.0, True, "say", 50))
        self.assertEqual(dict(s.voices), {})

    def test_env_beats_config(self):
        s = Settings.from_sources(
            {"api_key": "cfg", "model_id": "cfg", "default_voice": "cfg"},
            {"ELEVENLABS_API_KEY": "env", "ELEVENLABS_MODEL_ID": "env",
             "ELEVENLABS_VOICE_ID": "env"})
        self.assertEqual((s.api_key, s.model_id, s.default_voice), ("env", "env", "env"))

    def test_voice_priority(self):
        s = Settings.from_sources({"voices": {"warrior": "W"}, "default_voice": "D"}, {})
        self.assertEqual(s.voice_for(Persona("warrior", voice_id="P")), "W")
        self.assertEqual(s.voice_for(Persona("noir", voice_id="P")), "P")
        self.assertEqual(s.voice_for(Persona("noir")), "D")
        self.assertEqual(s.voice_for(None), "D")

    def test_settings_are_immutable(self):
        with self.assertRaises(AttributeError):
            Settings().rate = 2.0
        with self.assertRaises(TypeError):
            Settings.from_sources({"voices": {"a": "b"}}, {}).voices["c"] = "d"


class StateTest(unittest.TestCase):
    def test_garbage_gives_defaults(self):
        self.assertEqual(State.from_dict({"persona": 5, "voice": "on"}), State())

    def test_speaking_needs_persona_and_voice(self):
        self.assertFalse(State().speaking)
        self.assertTrue(State("noir").speaking)
        self.assertFalse(State("noir", voice=False).speaking)

    def test_updates_return_new_objects(self):
        state = State("noir")
        self.assertEqual(state.with_voice(False), State("noir", False))
        self.assertEqual(state, State("noir"))


class PersonaTest(unittest.TestCase):
    TEXT = ("---\ndescription: Воин\nvoice_id:\nsay_idle: Жду приказа.\n---\n"
            "You are a warrior.\n")

    def test_parse(self):
        p = Persona.parse("warrior", self.TEXT)
        self.assertEqual((p.description, p.prompt, p.voice_id), ("Воин", "You are a warrior.", None))
        self.assertEqual(p.phrase("idle"), "Жду приказа.")
        self.assertEqual(p.phrase("permission"), "Нужно твоё разрешение.")

    def test_without_frontmatter(self):
        self.assertEqual(Persona.parse("x", "  just text  ").prompt, "just text")

    def test_context_with_and_without_voice(self):
        p = Persona.parse("warrior", self.TEXT)
        self.assertIn("<speak>", p.context(with_voice=True))
        self.assertNotIn("<speak>", p.context(with_voice=False))
        self.assertTrue(p.context(False).startswith("[voice-personas] Active persona: warrior"))


class SpeechTest(unittest.TestCase):
    def test_find_lines_with_stable_keys(self):
        blocks = [TextBlock("3:0", "<speak>а</speak> и <SPEAK>б</SPEAK>")]
        self.assertEqual(find_speak_lines(blocks), [("3:0:0", "а"), ("3:0:1", "б")])

    def test_select_new_skips_seen(self):
        sel = select_new([("k1", "раз"), ("k2", "два")], seen=("k1",))
        self.assertEqual((sel.to_say, sel.seen), (("два",), ("k1", "k2")))

    def test_select_new_says_only_last_but_marks_all(self):
        lines = [(f"k{i}", f"реплика {i}") for i in range(5)]
        sel = select_new(lines, seen=())
        self.assertEqual(sel.to_say, ("реплика 2", "реплика 3", "реплика 4"))
        self.assertEqual(len(sel.seen), 5)

    def test_clean(self):
        self.assertEqual(clean_spoken("**Готово** см. https://x.io `код`"), "Готово см. код")
        self.assertEqual(len(clean_spoken("а" * 1000)), MAX_SPOKEN_CHARS)

    def test_too_short_lines_dropped(self):
        self.assertEqual(select_new([("k", " * ")], ()).to_say, ())


class NotificationTest(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify_notification({"notification_type": "permission_prompt"}),
                         "permission")
        self.assertEqual(classify_notification(
            {"message": "Claude needs your permission to use Bash"}), "permission")
        self.assertEqual(classify_notification(
            {"message": "Claude is waiting for your input"}), "idle")
        self.assertIsNone(classify_notification({"message": "auth ok"}))


if __name__ == "__main__":
    unittest.main()
