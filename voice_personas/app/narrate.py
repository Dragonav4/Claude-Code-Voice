"""PostToolUse and Stop: find new spoken lines and queue them for speech.

Mode "all" speaks after every tool call; mode "end" speaks only the last line on Stop.
Both respect max_lines_per_turn, which on_prompt resets (#3).
"""

import time
from pathlib import Path

from ..domain import find_speak_lines, select_new
from ..domain.speech import MAX_LINES_PER_RUN

STOP_RETRY_DELAY_S = 0.4  # the final message is sometimes not yet in the transcript


def _run_limit(app, mode, session):
    remaining = max(app.settings.max_lines_per_turn - app.store.load_turn_count(session), 0)
    return min(1 if mode == "end" else MAX_LINES_PER_RUN, remaining)


def collect_new_lines(app, transcript, session, mode):
    # Stop and PostToolUse may fire almost together: never speak a line twice.
    with app.store.lock("collect"):
        lines = find_speak_lines(app.read_transcript(transcript))
        limit = _run_limit(app, mode, session)
        selection = select_new(lines, app.store.load_seen(session), limit=limit)
        app.store.save_seen(session, selection.seen)
        spoken = app.store.load_turn_count(session) + len(selection.to_say)
        app.store.save_turn_count(session, spoken)
    return selection.to_say


def narrate(app, payload):
    state = app.store.load_state()
    transcript = payload.get("transcript_path")
    is_stop = payload.get("hook_event_name") == "Stop"
    if not state.speaking or not transcript or (state.narration == "end" and not is_stop):
        return None
    path = Path(str(transcript)).expanduser()
    session = str(payload.get("session_id") or "unknown")

    texts = collect_new_lines(app, path, session, state.narration)
    if not texts and is_stop:
        time.sleep(STOP_RETRY_DELAY_S)
        texts = collect_new_lines(app, path, session, state.narration)
    if texts:
        app.queue.enqueue(state.persona, texts)
    return None
