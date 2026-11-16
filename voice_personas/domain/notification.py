"""Claude Code notification kind: waiting for permission or for input."""


def classify_notification(payload):
    """ "permission", "idle" or None."""
    kind = str(payload.get("notification_type") or "")
    message = str(payload.get("message") or "").lower()
    if kind == "permission_prompt" or "permission" in message:
        return "permission"
    if kind == "idle_prompt" or "waiting for your input" in message:
        return "idle"
    return None
