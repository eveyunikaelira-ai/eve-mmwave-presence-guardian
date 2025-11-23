"""Background service orchestrating radar reads and presence tracking."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .radar import RD03DRadar
from .state import PresenceTracker

logger = logging.getLogger(__name__)


class RadarService:
    def __init__(self, radar: RD03DRadar, tracker: PresenceTracker) -> None:
        self.radar = radar
        self.tracker = tracker
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            await self._task
        self.radar.close()

    async def _run(self) -> None:
        try:
            self.radar.connect()
        except Exception:
            logger.exception("Failed to connect to RD-03D. Retrying in 5 seconds.")
            await asyncio.sleep(5)
            return await self._run()

        while not self._stop_event.is_set():
            try:
                detection = await self.radar.read_detection()
                if detection:
                    await self.tracker.mark_present(detection.distance_m)
                await self.tracker.mark_absent_if_needed()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error reading from radar; continuing loop")
                await asyncio.sleep(1)
            await asyncio.sleep(0)

        logger.info("Radar service stopped")
