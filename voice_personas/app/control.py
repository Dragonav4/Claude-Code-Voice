"""/persona and /voice commands. Each returns (exit code, text for the user)."""

TEST_PHRASE = "Проверка связи. Голос на месте."
VOICE_USAGE = "Используй: /voice on | off | status | stop | test [текст] | mode all|end"
MODE_NAMES = {"all": "каждый шаг", "end": "только в конце хода"}
PERSONA_OFF = ("off", "none", "reset")


def _yes_no(flag):
    return "да" if flag else "нет"


def list_personas(app):
    state = app.store.load_state()
    lines = ["Доступные персоны:"]
    for name, persona in app.personas.all().items():
        mark = " (активна)" if state.persona == name else ""
        lines.append(f"- {name}{mark}: {persona.description}")
    if state.persona is None:
        lines.append("Сейчас: без персоны.")
    lines.append("Выбрать: /persona <имя>, выключить: /persona off")
    return 0, "\n".join(lines)


def persona_command(app, arg):
    name = arg.strip().lower()
    if name in ("", "list"):
        return list_personas(app)
    state = app.store.load_state()
    if name in PERSONA_OFF:
        app.store.save_state(state.with_persona(None))
        return 0, "Персона выключена."
    available = app.personas.all()
    if name not in available:
        return 1, f"Нет персоны '{name}'. Доступно: {', '.join(available)}"
    app.store.save_state(state.with_persona(name))
    return 0, f"Персона: {name}. Применится со следующего сообщения."


def status_text(app):
    state = app.store.load_state()
    s = app.settings
    voice_id = s.voice_for(app.personas.get(state.persona))
    return "\n".join(
        [
            f"Персона: {state.persona or 'нет'}",
            f"Озвучка: {'вкл' if state.voice else 'выкл'}",
            f"Режим озвучки: {MODE_NAMES[state.narration]}, "
            f"не больше {s.max_lines_per_turn} реплик за ход",
            f"ElevenLabs API key: {'найден' if s.api_key else 'НЕ найден'}",
            f"Voice ID: {voice_id or 'НЕ задан'}",
            f"Модель: {s.model_id}, скорость {s.rate}, громкость {s.volume}",
            f"Запасной голос: {s.fallback} ({s.fallback_voice or 'по языку реплики'})",
            f"Обрыв речи новым сообщением: {_yes_no(s.interrupt_on_prompt)}",
            f"Голосовые уведомления: {_yes_no(s.notifications)}",
            f"Приглушение Music: {_yes_no(s.duck_music)}",
            f"Лог ошибок озвучки: {app.paths.log_file}",
            f"Конфиг: {app.paths.config_file}",
        ]
    )


def send_test_phrase(app, text):
    state = app.store.load_state()
    if not state.speaking:
        return 1, "Сначала выбери персону и включи озвучку: /persona <имя>, /voice on"
    app.queue.enqueue(state.persona, [text.strip() or TEST_PHRASE])
    return 0, "Тестовая фраза отправлена. Тишина — смотри лог из /voice status."


def set_mode(app, mode):
    if mode not in MODE_NAMES:
        return 1, "Используй: /voice mode all (каждый шаг) | end (только в конце хода)"
    app.store.save_state(app.store.load_state().with_narration(mode))
    return 0, f"Режим озвучки: {MODE_NAMES[mode]}. Применится со следующего сообщения."


def voice_command(app, arg):
    command, _, rest = arg.strip().partition(" ")
    command = command.lower()
    if command in ("", "status"):
        return 0, status_text(app)
    if command == "stop":
        return 0, f"Остановлено реплик: {app.queue.stop_all()}."
    if command == "test":
        return send_test_phrase(app, rest)
    if command == "mode":
        return set_mode(app, rest.strip().lower())
    if command not in ("on", "off"):
        return 1, VOICE_USAGE
    app.store.save_state(app.store.load_state().with_voice(command == "on"))
    return 0, f"Озвучка: {'вкл' if command == 'on' else 'выкл'}."


COMMANDS = {
    "persona": persona_command,
    "voice": voice_command,
    "status": lambda app, _: (0, status_text(app)),
}
USAGE = "Использование: ctl.py persona [list|<имя>|off] | voice [on|off|status|stop|test] | status"


def run_command(app, argv):
    if not argv or argv[0] not in COMMANDS:
        return 1, USAGE
    return COMMANDS[argv[0]](app, " ".join(argv[1:]))
