"""UserPromptSubmit: оборвать недоговорённую речь и напомнить Claude про персону."""


def on_prompt(app, payload):
    """Возвращает текст для контекста Claude или None."""
    if app.settings.interrupt_on_prompt:
        app.queue.stop_all()
    state = app.store.load_state()
    persona = app.personas.get(state.persona)
    return persona.context(with_voice=state.voice) if persona else None
