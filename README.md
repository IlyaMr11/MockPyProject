# OpsMonitor Benchmark Service

`OpsMonitor` is a compact Python backend used as a benchmark source for AI code review.
The service models a small device monitoring API with:

- device inventory management
- event ingestion
- token-based access control
- cached fleet summary responses
- SQLite-backed repositories
- pagination and filtering

The `main` branch stays runnable and intentionally clean. Benchmark pull requests live as
separate branches and are also described in `benchmark/`.

## Architecture

The project uses a small service-oriented layout:

- `src/opsmonitor/api/` HTTP handlers and dependency wiring
- `src/opsmonitor/services/` business logic
- `src/opsmonitor/repositories/` SQLite data access
- `src/opsmonitor/models/` request and response schemas
- `src/opsmonitor/utils/` cache and pagination helpers
- `tests/` API-level coverage for the clean baseline

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
uvicorn opsmonitor.app:app --reload
```

The app starts with seeded demo data and these local tokens:

- `reader-demo-token` with `read`
- `writer-demo-token` with `read,write`
- `admin-demo-token` with `read,write,admin`

Use them through the `X-Api-Key` header.

## Test

```bash
pytest
```

## Example Requests

```bash
curl -H "X-Api-Key: reader-demo-token" http://127.0.0.1:8000/devices
curl -H "X-Api-Key: writer-demo-token" \
  -H "Content-Type: application/json" \
  -d '{"external_id":"edge-gw-9","name":"Edge Gateway 9","site":"ams-1","owner_team":"ops"}' \
  http://127.0.0.1:8000/devices
```
