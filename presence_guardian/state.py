"""Presence tracking and change detection."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from .persistence import PresenceEvent, PresenceRepository


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class PresenceSnapshot:
    present: bool
    last_seen: Optional[str]
    last_distance_m: Optional[float]
    note: Optional[str] = None


class PresenceTracker:
    """Tracks the current state of occupancy and emits changes."""

    def __init__(
        self,
        inactivity_timeout: float,
        hysteresis_m: float,
        repo: PresenceRepository,
        log_note: Optional[str] = None,
    ) -> None:
        self.inactivity_timeout = timedelta(seconds=inactivity_timeout)
        self.hysteresis_m = hysteresis_m
        self.repo = repo
        self.log_note = log_note
        self._present: bool = False
        self._last_seen: Optional[datetime] = None
        self._last_distance: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def snapshot(self) -> PresenceSnapshot:
        return PresenceSnapshot(
            present=self._present,
            last_seen=self._last_seen.isoformat() if self._last_seen else None,
            last_distance_m=self._last_distance,
            note=self.log_note,
        )

    async def mark_present(self, distance_m: float) -> None:
        async with self._lock:
            change_detected = False
            if not self._present:
                self._present = True
                change_detected = True
            if self._last_distance is None or abs(self._last_distance - distance_m) > self.hysteresis_m:
                self._last_distance = distance_m
                change_detected = True
            self._last_seen = _utc_now()
            if change_detected:
                self.repo.log_event(True, self._last_distance, self.log_note)

    async def mark_absent_if_needed(self) -> None:
        async with self._lock:
            if not self._present or not self._last_seen:
                return
            if _utc_now() - self._last_seen >= self.inactivity_timeout:
                self._present = False
                self.repo.log_event(False, self._last_distance, self.log_note)

    async def force_absent(self) -> None:
        async with self._lock:
            self._present = False
            self.repo.log_event(False, self._last_distance, self.log_note)
            self._last_seen = _utc_now()

    async def latest_event(self) -> Optional[PresenceEvent]:
        return self.repo.latest()

    async def recent_events(self, limit: int = 50):
        return self.repo.fetch_recent(limit=limit)
