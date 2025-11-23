"""FastAPI application exposing the presence data."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from .persistence import PresenceRepository
from .service import RadarService
from .state import PresenceTracker


class _Dependencies:
    def __init__(self, tracker: PresenceTracker, repo: PresenceRepository) -> None:
        self.tracker = tracker
        self.repo = repo


async def get_deps(deps: _Dependencies = Depends()):  # type: ignore[override]
    return deps


def create_app(tracker: PresenceTracker, repo: PresenceRepository, service: RadarService) -> FastAPI:
    deps = _Dependencies(tracker, repo)
    app = FastAPI(title="RD-03D Presence Guardian", version="1.0.0")

    @app.on_event("startup")
    async def _startup() -> None:
        await service.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await service.stop()

    @app.get("/status")
    async def get_status(dep: _Dependencies = Depends(get_deps)):
        snapshot = dep.tracker.snapshot
        return {
            "present": snapshot.present,
            "last_seen": snapshot.last_seen,
            "last_distance_m": snapshot.last_distance_m,
            "note": snapshot.note,
        }

    @app.get("/events")
    async def list_events(limit: int = 50, dep: _Dependencies = Depends(get_deps)):
        events = await dep.tracker.recent_events(limit=limit)
        return [
            {
                "timestamp": e.timestamp,
                "present": e.present,
                "distance_m": e.distance_m,
                "note": e.note,
            }
            for e in events
        ]

    @app.get("/events/latest")
    async def latest_event(dep: _Dependencies = Depends(get_deps)):
        event = await dep.tracker.latest_event()
        if not event:
            return JSONResponse(status_code=404, content={"detail": "No events recorded"})
        return {
            "timestamp": event.timestamp,
            "present": event.present,
            "distance_m": event.distance_m,
            "note": event.note,
        }

    return app
