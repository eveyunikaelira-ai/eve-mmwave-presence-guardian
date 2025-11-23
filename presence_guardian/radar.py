"""RD-03D mmWave radar reader utilities."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import serial

logger = logging.getLogger(__name__)


@dataclass
class RadarDetection:
    """Structured reading from the RD-03D sensor."""

    distance_m: float
    energy: Optional[float] = None


class RD03DRadar:
    """Minimal RD-03D UART reader.

    The module expects the RD-03D to emit comma-separated frames such as
    ``"0.87,58"`` where the first value is meters and the second is an optional
    energy/confidence value. The parser is intentionally permissive so the
    service can keep running even if the radar produces occasional malformed
    frames.
    """

    def __init__(self, port: str, baud_rate: int = 115200) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self._serial: Optional[serial.Serial] = None

    def connect(self) -> None:
        if self._serial and self._serial.is_open:
            return
        self._serial = serial.Serial(self.port, self.baud_rate, timeout=1)
        logger.info("Opened RD-03D on %s @ %s baud", self.port, self.baud_rate)

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Closed RD-03D serial connection")

    def _readline(self) -> Optional[str]:
        if not self._serial:
            return None
        raw = self._serial.readline()
        if not raw:
            return None
        try:
            return raw.decode("utf-8", errors="ignore").strip()
        except UnicodeDecodeError:
            logger.debug("Failed to decode radar frame: %s", raw)
            return None

    def parse_frame(self, frame: str) -> Optional[RadarDetection]:
        if not frame:
            return None
        try:
            parts = [p.strip() for p in frame.split(",") if p.strip()]
            if not parts:
                return None
            distance = float(parts[0])
            energy = float(parts[1]) if len(parts) > 1 else None
            return RadarDetection(distance_m=distance, energy=energy)
        except (ValueError, IndexError):
            logger.debug("Ignoring invalid radar frame: %s", frame)
            return None

    async def read_detection(self) -> Optional[RadarDetection]:
        """Blocking serial read bridged into asyncio."""

        def _blocking_read() -> Optional[str]:
            if not self._serial:
                return None
            return self._readline()

        frame = await asyncio.to_thread(_blocking_read)
        if frame is None:
            return None
        return self.parse_frame(frame)

    async def __aenter__(self) -> "RD03DRadar":
        self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


async def poll_radar(sensor: RD03DRadar) -> Optional[RadarDetection]:
    """Convenience helper for a single radar poll."""

    return await sensor.read_detection()
