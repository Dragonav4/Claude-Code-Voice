"""/persona and /narrate commands. Each returns (exit code, text for the user)."""

TEST_PHRASE = "Voice check. Can you hear me?"
VOICE_USAGE = "Usage: /narrate on | off | status | stop | test [text] | mode all|end"
MODE_NAMES = {"all": "every step", "end": "end of turn only"}
PERSONA_OFF = ("off", "none", "reset")
NEXT_MESSAGE = "Takes effect from the next message."


def _yes_no(flag):
    return "yes" if flag else "no"


def _on_off(flag):
    return "on" if flag else "off"


def list_personas(app):
    state = app.store.load_state()
    lines = ["Personas:"]
    for name, persona in app.personas.all().items():
        mark = " (active)" if state.persona == name else ""
        lines.append(f"- {name}{mark}: {persona.description}")
    if state.persona is None:
        lines.append("Now: no persona.")
    lines.append("Use: /persona <name>, turn off: /persona off, bring back: /persona on")
    return 0, "\n".join(lines)


def persona_command(app, arg):
    name = arg.strip().lower()
    if name in ("", "list"):
        return list_personas(app)
    state = app.store.load_state()
    if name in PERSONA_OFF:
        app.store.save_state(state.with_persona(None))
        return 0, "Persona off."
    if name == "on":
        return restore_persona(app, state)
    available = app.personas.all()
    persona = next((p for p in available.values() if p.answers_to(name)), None)
    if persona is None:
        return 1, f"No persona '{name}'. Available: {', '.join(available)}"
    return select_persona(app, state, persona.name)


def select_persona(app, state, name):
    app.store.save_state(state.with_persona(name))
    return 0, f"Persona: {name}. {NEXT_MESSAGE}"


def restore_persona(app, state):
    if state.persona:
        return 0, f"Persona {state.persona} is already on."
    if app.personas.get(state.last_persona) is None:
        return 1, "No persona was selected yet: /persona <name>"
    return select_persona(app, state, state.last_persona)


def status_text(app):
    state = app.store.load_state()
    s = app.settings
    voice_id = s.voice_for(app.personas.get(state.persona))
    return "\n".join(
        [
            f"Persona: {state.persona or 'none'}",
            f"Narration: {_on_off(state.voice)}",
            f"Narration mode: {MODE_NAMES[state.narration]}, "
            f"at most {s.max_lines_per_turn} lines per turn",
            f"ElevenLabs API key: {'found' if s.api_key else 'NOT found'}",
            f"Voice ID: {voice_id or 'NOT set'}",
            f"Model: {s.model_id}, rate {s.rate}, volume {s.volume}",
            f"Fallback voice: {s.fallback} ({s.fallback_voice or 'by line language'})",
            f"New prompt cuts off speech: {_yes_no(s.interrupt_on_prompt)}",
            f"Voice notifications: {_yes_no(s.notifications)}",
            f"Duck Music: {_yes_no(s.duck_music)}",
            f"Error log: {app.paths.log_file}",
            f"Config: {app.paths.config_file}",
        ]
    )


def send_test_phrase(app, text):
    state = app.store.load_state()
    if not state.speaking:
        return 1, "Pick a persona and turn narration on first: /persona <name>, /narrate on"
    app.queue.enqueue(state.persona, [text.strip() or TEST_PHRASE])
    return 0, "Test line sent. Silence? Check the log from /narrate status."


def set_mode(app, mode):
    if mode not in MODE_NAMES:
        return 1, "Usage: /narrate mode all (every step) | end (end of turn only)"
    app.store.save_state(app.store.load_state().with_narration(mode))
    return 0, f"Narration mode: {MODE_NAMES[mode]}. {NEXT_MESSAGE}"


def voice_command(app, arg):
    command, _, rest = arg.strip().partition(" ")
    command = command.lower()
    if command in ("", "status"):
        return 0, status_text(app)
    if command == "stop":
        return 0, f"Lines stopped: {app.queue.stop_all()}."
    if command == "test":
        return send_test_phrase(app, rest)
    if command == "mode":
        return set_mode(app, rest.strip().lower())
    if command not in ("on", "off"):
        return 1, VOICE_USAGE
    app.store.save_state(app.store.load_state().with_voice(command == "on"))
    return 0, f"Narration: {command}."


COMMANDS = {
    "persona": persona_command,
    "narrate": voice_command,
    "voice": voice_command,  # commands/voice.md of plugin versions before 0.5
    "status": lambda app, _: (0, status_text(app)),
}
USAGE = (
    "Usage: ctl.py persona [list|<name>|on|off] | narrate [on|off|status|stop|test|mode] | status"
)


def run_command(app, argv):
    if not argv or argv[0] not in COMMANDS:
        return 1, USAGE
    return COMMANDS[argv[0]](app, " ".join(argv[1:]))
