"""SQLite persistence for presence events."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class PresenceEvent:
    timestamp: str
    present: bool
    distance_m: Optional[float]
    note: Optional[str] = None


class PresenceRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL;")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                present INTEGER NOT NULL,
                distance_m REAL,
                note TEXT
            );
            """
        )
        self._connection.commit()

    def log_event(self, present: bool, distance_m: Optional[float], note: Optional[str]) -> int:
        cur = self._connection.execute(
            "INSERT INTO events(timestamp, present, distance_m, note) VALUES(?, ?, ?, ?);",
            (utc_now_iso(), int(present), distance_m, note),
        )
        self._connection.commit()
        return int(cur.lastrowid)

    def fetch_recent(self, limit: int = 50) -> List[PresenceEvent]:
        cur = self._connection.execute(
            "SELECT timestamp, present, distance_m, note FROM events ORDER BY id DESC LIMIT ?;",
            (limit,),
        )
        rows = cur.fetchall()
        return [
            PresenceEvent(
                timestamp=row[0], present=bool(row[1]), distance_m=row[2], note=row[3]
            )
            for row in rows
        ]

    def latest(self) -> Optional[PresenceEvent]:
        cur = self._connection.execute(
            "SELECT timestamp, present, distance_m, note FROM events ORDER BY id DESC LIMIT 1;"
        )
        row = cur.fetchone()
        if not row:
            return None
        return PresenceEvent(
            timestamp=row[0], present=bool(row[1]), distance_m=row[2], note=row[3]
        )

    def close(self) -> None:
        self._connection.close()
