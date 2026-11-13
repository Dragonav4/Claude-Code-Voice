"""Воркер: озвучить реплики по очереди. ElevenLabs, при неудаче — `say`."""
import os


def speak_line(app, text, voice_id):
    path = app.synth.audio_file(text, voice_id)
    if path:
        app.player.play_file(path)
    elif app.settings.fallback == "say":
        app.player.say(text)


def speak_job(app, job):
    texts = [text for text in job.get("texts") or [] if isinstance(text, str) and text]
    voice_id = app.settings.voice_for(app.personas.get(job.get("persona")))
    settings = app.settings
    with app.queue.registered(os.getpid()):     # видим для обрыва, даже пока ждём очереди
        with app.store.lock("speak"):           # реплики не накладываются
            with app.ducked(settings.duck_music, settings.duck_volume):
                for text in texts:
                    speak_line(app, text, voice_id)
