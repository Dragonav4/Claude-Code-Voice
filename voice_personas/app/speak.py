"""Worker: speak lines one by one. ElevenLabs, falling back to the system voice."""

import os

from ..domain import strip_audio_tags, supports_audio_tags


def speak_line(app, text, voice_id):
    plain = strip_audio_tags(text)
    tagged = supports_audio_tags(app.settings.model_id)
    path = app.synth.audio_file(text if tagged else plain, voice_id)
    if path:
        app.player.play_file(path)
    elif app.settings.fallback == "say":
        app.player.say(plain)  # a system voice would read "[laughs]" as a word


def speak_job(app, job):
    texts = [text for text in job.get("texts") or [] if isinstance(text, str) and text]
    voice_id = app.settings.voice_for(app.personas.get(job.get("persona")))
    settings = app.settings
    with app.queue.registered(os.getpid()):  # can be stopped even while waiting in the queue
        with app.store.lock("speak"):  # lines never overlap
            with app.ducked(settings.duck_music, settings.duck_volume):
                for text in texts:
                    speak_line(app, text, voice_id)
