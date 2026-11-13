"""PostToolUse и Stop: найти новые реплики <speak> и отправить их в очередь озвучки."""
import time
from pathlib import Path

from ..domain import find_speak_lines, select_new

STOP_RETRY_DELAY_S = 0.4  # финальное сообщение иногда ещё не дописано в транскрипт


def collect_new_lines(app, transcript, session):
    # Stop и PostToolUse могут сработать почти одновременно — не дублируем реплики.
    with app.store.lock("collect"):
        lines = find_speak_lines(app.read_transcript(transcript))
        selection = select_new(lines, app.store.load_seen(session))
        app.store.save_seen(session, selection.seen)
    return selection.to_say


def narrate(app, payload):
    state = app.store.load_state()
    transcript = payload.get("transcript_path")
    if not state.speaking or not transcript:
        return None
    path = Path(str(transcript)).expanduser()
    session = str(payload.get("session_id") or "unknown")

    texts = collect_new_lines(app, path, session)
    if not texts and payload.get("hook_event_name") == "Stop":
        time.sleep(STOP_RETRY_DELAY_S)
        texts = collect_new_lines(app, path, session)
    if texts:
        app.queue.enqueue(state.persona, texts)
    return None
