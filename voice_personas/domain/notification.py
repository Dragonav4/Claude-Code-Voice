"""Тип уведомления Claude Code: ждёт разрешения или ждёт ввода."""


def classify_notification(payload):
    """"permission", "idle" или None."""
    kind = str(payload.get("notification_type") or "")
    message = str(payload.get("message") or "").lower()
    if kind == "permission_prompt" or "permission" in message:
        return "permission"
    if kind == "idle_prompt" or "waiting for your input" in message:
        return "idle"
    return None
