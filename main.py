"""Entry point for the RD-03D presence guardian."""

from __future__ import annotations

import logging

import uvicorn

from presence_guardian.api import create_app
from presence_guardian.config import AppConfig
from presence_guardian.persistence import PresenceRepository
from presence_guardian.radar import RD03DRadar
from presence_guardian.service import RadarService
from presence_guardian.state import PresenceTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_components(config: AppConfig):
    repo = PresenceRepository(config.sqlite_path)
    tracker = PresenceTracker(
        inactivity_timeout=config.inactivity_timeout_s,
        hysteresis_m=config.detection_hysteresis_m,
        repo=repo,
        log_note=config.log_notes,
    )
    radar = RD03DRadar(config.serial_port, baud_rate=config.baud_rate)
    service = RadarService(radar=radar, tracker=tracker)
    return repo, tracker, radar, service


config = AppConfig.from_env()
_repo, _tracker, _radar, _service = build_components(config)
app = create_app(tracker=_tracker, repo=_repo, service=_service)


def run_server(config: AppConfig) -> None:
    uvicorn.run(app, host=config.api_host, port=config.api_port)


if __name__ == "__main__":
    run_server(config)
