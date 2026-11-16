import re
import unittest

import support
from voice_personas.app.control import run_command
from voice_personas.domain import Persona, State


class NarrateCommandTest(support.TempHomeTest):
    def test_narrate_is_the_command(self):
        app = self.app()
        self.assertEqual(run_command(app, ["narrate", "off"]), (0, "Narration: off."))
        self.assertFalse(app.store.load_state().voice)

    def test_voice_still_works_for_old_installs(self):
        self.assertEqual(run_command(self.app(), ["voice", "on"]), (0, "Narration: on."))

    def test_user_text_never_points_to_the_builtin_voice(self):
        app = self.app()
        texts = [
            run_command(app, ["narrate", "loud"])[1],
            run_command(app, ["narrate", "test"])[1],
            run_command(app, ["narrate", "mode", "loud"])[1],
            run_command(app, ["persona", "list"])[1],
        ]
        for text in texts:
            self.assertNotIn("/voice", text)

    def test_command_files(self):
        commands = support.ROOT / "commands"
        self.assertTrue((commands / "narrate.md").is_file())
        self.assertFalse((commands / "voice.md").exists())


class PersonaOnTest(support.TempHomeTest):
    def test_on_restores_the_last_persona(self):
        app = self.app()
        run_command(app, ["persona", "noir"])
        run_command(app, ["persona", "off"])
        self.assertEqual(run_command(app, ["persona", "on"])[0], 0)
        self.assertEqual(app.store.load_state().persona, "noir")

    def test_on_without_history_explains(self):
        code, text = run_command(self.app(), ["persona", "on"])
        self.assertEqual(code, 1)
        self.assertIn("/persona <name>", text)

    def test_state_remembers_the_last_persona(self):
        state = State().with_persona("noir").with_persona(None)
        self.assertEqual((state.persona, state.last_persona), (None, "noir"))
        self.assertEqual(State.from_dict(state.to_dict()), state)

    def test_old_state_file_has_no_last_persona(self):
        self.assertIsNone(State.from_dict({"persona": None}).last_persona)


class PersonaAliasTest(support.TempHomeTest):
    def test_russian_name(self):
        app = self.app()
        self.assertEqual(run_command(app, ["persona", "Цундере"])[0], 0)
        self.assertEqual(app.store.load_state().persona, "tsundere")

    def test_every_builtin_persona_has_a_russian_alias(self):
        for name, persona in self.app().personas.all().items():
            self.assertTrue(persona.aliases, name)

    def test_aliases_parse(self):
        persona = Persona.parse("x", "---\naliases: Икс, игрек\n---\nbody")
        self.assertEqual(persona.aliases, ("икс", "игрек"))
        self.assertTrue(persona.answers_to("ИКС"))
        self.assertTrue(persona.answers_to("x"))


class EnglishOnlyTest(unittest.TestCase):
    """Everything outside personas/ is English; tests may feed Cyrillic as input data."""

    def test_no_cyrillic_outside_personas(self):
        cyrillic = re.compile("[\u0400-\u04ff]")
        allowed = {"voice_personas/domain/language.py"}  # detects Cyrillic on purpose
        roots = ["voice_personas", "bin", "commands", ".claude-plugin", "docs"]
        files = [p for r in roots for p in (support.ROOT / r).rglob("*") if p.is_file()]
        files += [support.ROOT / n for n in ("README.md", "CONVENTIONS.md", "pyproject.toml")]
        offenders = [
            str(p.relative_to(support.ROOT))
            for p in files
            if p.suffix in (".py", ".md", ".json", ".toml", ".sh")
            and p.relative_to(support.ROOT).as_posix() not in allowed
            and cyrillic.search(p.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
