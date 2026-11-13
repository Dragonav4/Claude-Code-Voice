"""UserPromptSubmit: cut off unfinished speech and remind Claude of the persona."""


def on_prompt(app, payload):
    """Returns text for Claude's context, or None."""
    if app.settings.interrupt_on_prompt:
        app.queue.stop_all()
    state = app.store.load_state()
    persona = app.personas.get(state.persona)
    return persona.context(with_voice=state.voice) if persona else None
