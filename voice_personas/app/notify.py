"""Notification: say out loud that Claude waits for permission or input."""

from ..domain import DEFAULT_PHRASES, classify_notification


def notify(app, payload):
    state = app.store.load_state()
    if not state.speaking or not app.settings.notifications:
        return None
    kind = classify_notification(payload)
    if kind is None:
        return None
    persona = app.personas.get(state.persona)
    phrase = persona.phrase(kind) if persona else DEFAULT_PHRASES[kind]
    app.queue.enqueue(state.persona, [phrase])
    return None
