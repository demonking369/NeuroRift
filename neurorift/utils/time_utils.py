from datetime import datetime, timezone


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()
