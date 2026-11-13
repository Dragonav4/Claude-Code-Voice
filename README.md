# Claude-Code-Voice

Плагин для Claude Code (macOS): персоны ответов (цундере, воин, дворецкий, нуар) и озвучка реплик персоны по ходу работы через ElevenLabs.

## Что умеет

- **Персоны.** `/persona <имя>` меняет тон ответов. Код, команды и коммиты остаются нейтральными.
- **Озвучка по ходу работы.** Перед действиями и в конце хода Claude пишет короткую реплику в `<speak>...</speak>`, плагин её озвучивает. Код, пути и логи наружу не уходят.
- **Обрыв речи.** Новое сообщение сразу обрывает недоговорённую реплику и очередь. Вручную: `/voice stop`.
- **Запасной голос.** Если нет ключа, кончились кредиты или нет сети, говорит системный `say` (по умолчанию русская Milena).
- **Голосовые уведомления.** «Нужно разрешение» и «жду тебя» звучат фразой в стиле персоны.
- **Кэш фраз.** Одинаковые реплики не синтезируются повторно и не тратят кредиты.
- **Скорость, громкость, приглушение Music.app** на время речи (выключено по умолчанию).

Зависимостей нет: только `python3` и встроенные `afplay`, `say`, `osascript`.

## Установка

```
claude plugin marketplace add /путь/к/Claude-Code-Voice
claude plugin install voice-personas@claude-code-voice
```

Ключ ElevenLabs задай в `~/.zshrc` (`export ELEVENLABS_API_KEY="..."`) или в `config.json` (см. ниже, тогда `chmod 600`). Если Claude Code запущен из старого окружения (tmux, IDE), надёжнее `config.json`.

Затем в Claude Code: `/persona list`, `/persona warrior`, `/voice test`.

## Команды

| Команда | Что делает |
|---|---|
| `/persona list` | список персон |
| `/persona <имя>` / `/persona off` | выбрать / выключить (со следующего сообщения) |
| `/voice on` / `/voice off` | включить / выключить озвучку |
| `/voice stop` | оборвать текущую речь |
| `/voice test [текст]` | проверить голос |
| `/voice status` | ключ, голос, настройки, путь к логу |

## Настройки

`~/.claude/voice-personas/config.json`, все поля необязательны:

```json
{
  "api_key": "...",
  "default_voice": "VOICE_ID",
  "voices": { "tsundere": "VOICE_ID_1", "warrior": "VOICE_ID_2" },
  "model_id": "eleven_multilingual_v2",
  "rate": 1.0,
  "volume": 1.0,
  "fallback": "say",
  "fallback_voice": "Milena",
  "interrupt_on_prompt": true,
  "notifications": true,
  "duck_music": false,
  "duck_volume": 20,
  "cache_mb": 50
}
```

- Порядок выбора голоса: `voices.<persona>`, затем `voice_id:` в файле персоны, затем `ELEVENLABS_VOICE_ID`, затем `default_voice`.
- `rate` от 0.5 до 2.0, `volume` от 0 до 1. Значения вне диапазона обрезаются.
- `fallback: "none"` — молчать, если ElevenLabs недоступен.
- `ELEVENLABS_API_KEY` и `ELEVENLABS_MODEL_ID` из окружения важнее конфига.

## Свои персоны

Файл `~/.claude/voice-personas/personas/<имя>.md` в формате файлов из `personas/`. Он перекрывает встроенную персону с тем же именем. В frontmatter можно задать `voice_id:`, `say_permission:` и `say_idle:` (фразы уведомлений).

## Отладка

- Ошибки озвучки пишутся в `~/.claude/voice-personas/speak.log`.
- `VOICE_PERSONAS_DRY_RUN=1` печатает реплики вместо синтеза и воспроизведения.
- Тесты: `python3 -m unittest discover -s tests -t tests`.

## Устройство кода

```
bin/                 точки входа: hooks и команды (по 10 строк)
voice_personas/
  domain/            чистая логика: настройки, персона, реплики, уведомления (без IO)
  app/               сценарии: narrate, notify, prompt, speak, control
    container.py     сборка зависимостей — единственное место, где app встречает infra
  infra/             внешний мир: файлы, транскрипт, ElevenLabs, afplay/say, Music, процессы
personas/            встроенные персоны
```

Зависимости направлены внутрь: `bin → app → domain`, а `infra` подключается только в `app/container.py` и `app/runner.py`. Сценарии получают всё через объект `App`, поэтому в тестах любую зависимость можно подменить.

Путь одной реплики: `bin/on_speak.py` → `app/narrate.py` (новые `<speak>` из транскрипта) → очередь → `bin/worker.py` → `app/speak.py` (ElevenLabs или `say`) → `infra/audio.py`.

## Известные ограничения

- Теги `<speak>` видны в тексте ответа.
- Если Claude не поставил `<speak>`, озвучки не будет. Это зависит от того, как модель следует промпту.
- Каждая реплика — отдельный платный запрос к ElevenLabs. Кэш помогает только для повторяющихся фраз.

## Идеи, взятые у других

Обрыв речи и ducking подсмотрены в [ktaletsk/claude-code-tts](https://github.com/ktaletsk/claude-code-tts), запасной голос и уведомления — в [ZeldOcarina/claude-code-voice-notifications](https://github.com/ZeldOcarina/claude-code-voice-notifications), скорость — в [cc-vox](https://github.com/BestSithInEU/cc-vox). Код написан заново.
