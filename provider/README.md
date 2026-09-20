# Provider

A FastAPI mock LLM provider used to test the [orchestrator](../orchestrator) under different service-health conditions. It exposes three independent FastAPI apps, each simulating a different reliability profile for the same `/api/v1/inference` endpoint.

## Simulated endpoints

| App | Script | Default port | Behavior |
|---|---|---|---|
| `full` (Active) | `run-full` | `8000` | Always returns `200`. Simulated latency: 3-5s. |
| `partial` (Partial) | `run-partial` | `8100` | ~30% chance of `429 Too Many Requests`, otherwise `200`. Simulated latency: 5-10s. |
| `inactive` (Inactive) | `run-inactive` | `8200` | ~20% chance of `500`, ~59% chance of `429`, otherwise `200`. Simulated latency: 10-15s. |

Each app exposes:

- `GET /health` — basic health check
- `GET /system_info` — version/author/status info
- `POST /api/v1/inference` — accepts `{"message": "<text>"}` and returns a random mock LLM response

## Requirements

| Requirement | Version |
|---|---|
| Python | >= 3.14 |
| Poetry | latest |

## Install

```bash
poetry install
```

## Configuration

Host/ports are read from `.env` at the project root (already present, defaults shown):

```ini
UVICORN_HOST=127.0.0.1
FULL_PORT=8000
PARTIAL_PORT=8100
INACTIVE_PORT=8200
```

`UVICORN_RELOAD` (default `true`) can also be set to enable/disable uvicorn's auto-reload.

## Usage

Run a single provider:

```bash
poetry run run-full      # Active   -> http://127.0.0.1:8000
poetry run run-partial   # Partial  -> http://127.0.0.1:8100
poetry run run-inactive  # Inactive -> http://127.0.0.1:8200
```

Or start all three together (each in its own subprocess, stopped together with Ctrl+C):

```bash
poetry run run-all
```

## Verifying it's running

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/system_info
```
