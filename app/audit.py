
"""Minimal append-only JSONL audit trail for the workshop.

The file is local and is not tamper-proof. Production audit storage
should use controlled access, retention policies and durable central storage.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parent.parent
AUDIT_FILE = ROOT / "data" / "audit.jsonl"
_AUDIT_LOCK = Lock()


def write_audit_event(
    event_type,
    outcome,
    correlation_id,
    incident_id=None,
    reason_code=None
):
    """Append a structured event without sensitive incident content."""
    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": str(event_type),
        "outcome": str(outcome),
        "correlation_id": str(correlation_id),
        "incident_id": (
            str(incident_id) if incident_id is not None else None
        ),
        "reason_code": (
            str(reason_code) if reason_code is not None else None
        )
    }

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, separators=(",", ":"), ensure_ascii=True)

    with _AUDIT_LOCK:
        with open(AUDIT_FILE, "a", encoding="utf-8") as file:
            file.write(line + "\n")
            file.flush()
            os.fsync(file.fileno())

    return event


def read_recent_audit_events(limit=100):
    """Return recent audit events, newest first."""
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer.")

    if not AUDIT_FILE.exists():
        return []

    lines = AUDIT_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    events = []

    for line in reversed(lines[-limit:]):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # Do not crash the dashboard on one damaged record.
            events.append({
                "event_type": "audit_record_error",
                "outcome": "invalid_json_line"
            })

    return events


def audit_summary():
    """Summarise recent events without exposing raw incident text."""
    events = read_recent_audit_events(limit=500)
    counts = {}

    for event in events:
        key = event.get("event_type", "unknown")
        counts[key] = counts.get(key, 0) + 1

    return {
        "file_exists": AUDIT_FILE.exists(),
        "events_in_summary": len(events),
        "events_by_type": counts,
        "latest_events": events[:10],
        "storage_scope": "local_jsonl_file"
    }
