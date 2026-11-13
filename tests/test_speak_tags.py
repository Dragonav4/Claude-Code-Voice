"""A reply that mentions the speak tag must not get spoken as a whole (#10)."""

import unittest

import support  # noqa: F401
from voice_personas.domain import Persona, TextBlock, find_speak_lines, select_new
from voice_personas.domain.speech import MAX_SPOKEN_CHARS

OPEN, CLOSE = "<speak>", "</speak>"


def spoken(text):
    lines = find_speak_lines([TextBlock("0:0", text)])
    return list(select_new(lines, seen=(), limit=10).to_say)


class MentionTest(unittest.TestCase):
    def test_mention_in_inline_code_is_ignored(self):
        reply = f"Claude adds a `{OPEN}` line. A long explanation. {OPEN}Готово{CLOSE}"
        self.assertEqual(spoken(reply), ["Готово"])

    def test_bare_mention_in_prose_does_not_swallow_the_reply(self):
        reply = f"Модель вставляет {OPEN} в ответ. Таблица, пути, код. {OPEN}Готово{CLOSE}"
        self.assertEqual(spoken(reply), ["Готово"])

    def test_both_tags_inside_inline_code_are_not_a_line(self):
        self.assertEqual(spoken(f"Пример: `{OPEN}текст{CLOSE}`."), [])

    def test_tags_inside_a_code_fence_are_ignored(self):
        reply = f"```\n{OPEN}из примера{CLOSE}\n```\n{OPEN}Да{CLOSE}"
        self.assertEqual(spoken(reply), ["Да"])

    def test_unclosed_fence_hides_the_rest(self):
        self.assertEqual(spoken(f"```\n{OPEN}x{CLOSE}"), [])


class SanityTest(unittest.TestCase):
    def test_too_long_line_is_rejected_not_truncated(self):
        self.assertEqual(spoken(OPEN + "слово " * 100 + CLOSE), [])
        self.assertEqual(spoken(OPEN + "а" * MAX_SPOKEN_CHARS + CLOSE), ["а" * MAX_SPOKEN_CHARS])

    def test_line_with_a_blank_line_is_rejected(self):
        self.assertEqual(spoken(f"{OPEN}Абзац один.\n\nАбзац два.{CLOSE}"), [])

    def test_normal_lines_still_work(self):
        reply = f"{OPEN}Начинаю.{CLOSE} работа {OPEN}Закончила.{CLOSE}"
        self.assertEqual(spoken(reply), ["Начинаю.", "Закончила."])


class RuleTest(unittest.TestCase):
    def test_model_is_told_not_to_write_the_tag_literally(self):
        context = Persona("noir", prompt="p").context(with_voice=True)
        self.assertIn("Never write the tag itself", context)


if __name__ == "__main__":
    unittest.main()
