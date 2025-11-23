# RD-03D Presence Guardian

Python service for Raspberry Pi 5 that streams RD-03D mmWave radar data over UART, tracks human presence/distance, records events to SQLite, and exposes a local REST API.

## Features
- Async UART reader for the RD-03D radar (pyserial) with tolerant frame parsing.
- Presence state tracking with inactivity timeout and distance hysteresis to avoid flapping.
- SQLite persistence of all presence transitions and distance updates.
- FastAPI REST endpoints for live status and historical events.
- Environment-based configuration suitable for systemd or container deployments.

## Requirements
- Python 3.10+
- Raspberry Pi 5 with RD-03D connected to a UART (default `/dev/ttyS0`).
- Dependencies listed in `requirements.txt` (install with `pip install -r requirements.txt`).

## Running
1. Configure the environment if needed:
   ```bash
   export RADAR_SERIAL_PORT=/dev/ttyAMA0  # adjust to your wiring
   export RADAR_BAUD_RATE=115200
   export INACTIVITY_TIMEOUT_S=30
   export DETECTION_HYSTERESIS_M=0.05
   export SQLITE_PATH=/var/lib/presence/events.db
   export API_HOST=0.0.0.0
   export API_PORT=8000
   ```

2. Launch the service:
   ```bash
   python -m uvicorn main:app --reload
   ```

   or simply run
   ```bash
   python main.py
   ```

3. Query the REST API locally:
   - `GET /status` — current presence, last seen, and last distance.
   - `GET /events?limit=50` — recent events (most recent first).
   - `GET /events/latest` — latest single event.

## How it works
- `presence_guardian/radar.py` handles UART connectivity and frame parsing from the RD-03D.
- `presence_guardian/state.py` debounces presence transitions and applies inactivity timeout/hysteresis.
- `presence_guardian/persistence.py` stores timestamped events in SQLite.
- `presence_guardian/service.py` runs the continuous radar poller.
- `presence_guardian/api.py` exposes the REST API and coordinates startup/shutdown of the radar loop.
- `main.py` wires everything together using environment-driven configuration (`AppConfig.from_env()`).

## SQLite schema
The SQLite database contains a single `events` table:
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    present INTEGER NOT NULL,
    distance_m REAL,
    note TEXT
);
```

`present` is stored as `1` (present) or `0` (absent), and `distance_m` represents the last measured distance in meters when available.
