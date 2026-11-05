import json

from datetime import datetime, timezone

from pathlib import Path

from threading import Lock


ROOT = Path(__file__).resolve().parent.parent

AUDIT_FILE = ROOT / "data" / "audit.jsonl"

_LOCK = Lock()


def record_event(
    event_type,
    incident_id=None,
    outcome=None,
    details=None
):

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "event_type": event_type,

        "incident_id": incident_id,

        "outcome": outcome,

        "details": details or {}
    }

    AUDIT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    line = json.dumps(
        event,
        ensure_ascii=False
    )

    with _LOCK:

        with AUDIT_FILE.open(
            "a",
            encoding="utf-8"
        ) as handle:

            handle.write(line + "\n")

    return event


def read_events(limit=100):

    if not AUDIT_FILE.exists():

        return []

    rows = []

    for line in AUDIT_FILE.read_text(
        encoding="utf-8"
    ).splitlines():

        try:

            rows.append(
                json.loads(line)
            )

        except json.JSONDecodeError:

            continue

    return rows[
        -max(1, min(int(limit), 500)):
    ]