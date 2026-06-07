"""İstemci, sunucu ve panel canlı akışları için JSONL olay günlüğü."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class EventLogger:
    def __init__(self, log_dir: str | Path, name: str, role: str) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
        self.path = self.log_dir / f"{safe_name}.jsonl"
        self.role = role
        self._lock = threading.Lock()

    def log(self, event: str, **fields: Any) -> dict[str, Any]:
        row = {
            "timestamp": utc_timestamp(),
            "monotonic": time.perf_counter(),
            "role": self.role,
            "event": event,
            **fields,
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row


def read_jsonl(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    lines = file_path.read_text(encoding="utf-8").splitlines()
    if limit is not None:
        lines = lines[-limit:]
    events: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def latest_event_files(log_dir: str | Path, limit: int = 8) -> list[Path]:
    root = Path(log_dir)
    if not root.exists():
        return []
    return sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def read_recent_events(log_dir: str | Path, limit: int = 120) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in latest_event_files(log_dir, limit=32):
        rows.extend(read_jsonl(path))
    rows.sort(key=lambda row: float(row.get("monotonic", 0.0)))
    return rows[-limit:]
