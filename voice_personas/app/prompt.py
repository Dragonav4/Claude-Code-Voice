"""UserPromptSubmit and SessionStart: cut off speech and keep Claude aware of the persona.

The full persona is sent once per session and after every change; other prompts get
a one-line reminder, so the history does not fill up with identical copies (#18).
"""


def _session(payload):
    session = payload.get("session_id")
    return str(session) if session else None


def persona_context(app, session):
    """The full persona text, a short reminder, or None when no persona is active."""
    state = app.store.load_state()
    persona = app.personas.get(state.persona)
    if persona is None:
        if session:
            app.store.clear_context_mark(session)
        return None
    if session is None:
        return persona.context(state.voice, state.narration)  # nowhere to remember it
    mark = persona.fingerprint(state.voice, state.narration)
    if app.store.load_context_mark(session) == mark:
        return persona.reminder(with_voice=state.voice)
    app.store.save_context_mark(session, mark)
    return persona.context(state.voice, state.narration)


def on_prompt(app, payload):
    """Returns text for Claude's context, or None."""
    if app.settings.interrupt_on_prompt:
        app.queue.stop_all()
    session = _session(payload)
    if session:
        app.store.save_turn_count(session, 0)  # a new turn starts the line limit over
    return persona_context(app, session)


def on_session_start(app, payload):
    """New, resumed, cleared or compacted session: the history may no longer hold the persona."""
    session = _session(payload)
    if session:
        app.store.clear_context_mark(session)
    return persona_context(app, session)
