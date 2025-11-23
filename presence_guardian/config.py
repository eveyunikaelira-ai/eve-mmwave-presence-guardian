"""Configuration helpers for the presence guardian service."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """Runtime configuration for the radar monitor and API server."""

    serial_port: str = "/dev/ttyS0"
    baud_rate: int = 115200
    inactivity_timeout_s: float = 30.0
    detection_hysteresis_m: float = 0.05
    sqlite_path: Path = Path("presence_events.db")
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_notes: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build configuration from environment variables when present."""

        import os

        return cls(
            serial_port=os.getenv("RADAR_SERIAL_PORT", cls.serial_port),
            baud_rate=int(os.getenv("RADAR_BAUD_RATE", cls.baud_rate)),
            inactivity_timeout_s=float(
                os.getenv("INACTIVITY_TIMEOUT_S", cls.inactivity_timeout_s)
            ),
            detection_hysteresis_m=float(
                os.getenv("DETECTION_HYSTERESIS_M", cls.detection_hysteresis_m)
            ),
            sqlite_path=Path(os.getenv("SQLITE_PATH", str(cls.sqlite_path))),
            api_host=os.getenv("API_HOST", cls.api_host),
            api_port=int(os.getenv("API_PORT", cls.api_port)),
            log_notes=os.getenv("EVENT_LOG_NOTES", cls.log_notes),
        )
