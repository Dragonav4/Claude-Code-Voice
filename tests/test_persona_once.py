"""The full persona goes into the context once per change, not on every prompt (#18)."""

import json
import subprocess
import sys

import support
from voice_personas.app.prompt import on_prompt, on_session_start
from voice_personas.domain import Persona, State

FULL_MARK = "Active persona:"


class OncePerSessionTest(support.TempHomeTest):
    def setUp(self):
        super().setUp()
        self.application = self.app()
        self.application.store.save_state(State("noir"))

    def prompt(self, session="s1"):
        return on_prompt(self.application, {"session_id": session})

    def test_full_text_first_then_a_short_reminder(self):
        self.assertIn(FULL_MARK, self.prompt())
        reminder = self.prompt()
        self.assertNotIn(FULL_MARK, reminder)
        self.assertLess(len(reminder), 300)
        self.assertIn("noir", reminder)

    def test_each_session_gets_its_own_full_text(self):
        self.prompt("s1")
        self.assertIn(FULL_MARK, self.prompt("s2"))

    def test_change_of_persona_or_voice_resends_the_full_text(self):
        self.prompt()
        self.application.store.save_state(State("butler"))
        self.assertIn("Active persona: butler", self.prompt())
        self.application.store.save_state(State("butler", voice=False))
        self.assertIn(FULL_MARK, self.prompt())

    def test_session_start_resets_after_clear_or_compaction(self):
        self.prompt()
        self.assertIn(FULL_MARK, on_session_start(self.application, {"session_id": "s1"}))
        self.assertNotIn(FULL_MARK, self.prompt())

    def test_without_a_session_id_always_full(self):
        self.assertIn(FULL_MARK, on_prompt(self.application, {}))
        self.assertIn(FULL_MARK, on_prompt(self.application, {}))

    def test_persona_off_then_on_resends(self):
        self.prompt()
        self.application.store.save_state(State(None))
        self.assertIsNone(self.prompt())
        self.application.store.save_state(State("noir"))
        self.assertIn(FULL_MARK, self.prompt())


class ReminderTest(support.TempHomeTest):
    def test_reminder_mentions_narration_only_with_voice(self):
        persona = Persona("noir", prompt="p")
        self.assertIn("speak tag", persona.reminder(with_voice=True))
        self.assertNotIn("speak tag", persona.reminder(with_voice=False))


class SessionHookTest(support.TempHomeTest):
    def test_session_hook_prints_the_persona(self):
        self.app().store.save_state(State("noir"))
        result = subprocess.run(
            [sys.executable, str(support.ROOT / "bin" / "on_session.py")],
            input=json.dumps({"session_id": "x", "source": "compact"}),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.env(),
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(FULL_MARK, result.stdout)
