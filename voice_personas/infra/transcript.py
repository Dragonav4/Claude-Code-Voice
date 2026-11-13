"""Чтение JSONL-транскрипта сессии Claude Code."""
import json

from ..domain import TextBlock


def _assistant_texts(record):
    """Тексты из одной записи транскрипта, если это сообщение ассистента."""
    if not isinstance(record, dict):
        return []
    message = record.get("message") if isinstance(record.get("message"), dict) else {}
    if record.get("type") != "assistant" and message.get("role") != "assistant":
        return []
    content = message.get("content", record.get("content"))
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [block.get("text", "") for block in content
                if isinstance(block, dict) and block.get("type") == "text"]
    return []


def read_text_blocks(path):
    """[TextBlock] ассистента. Ключ блока — "номер_строки:номер_блока"."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    blocks = []
    for line_no, line in enumerate(lines):
        try:
            record = json.loads(line)
        except ValueError:
            continue  # недописанная строка подхватится при следующем запуске
        blocks.extend(
            TextBlock(key=f"{line_no}:{index}", text=text)
            for index, text in enumerate(_assistant_texts(record))
            if isinstance(text, str) and text
        )
    return blocks
