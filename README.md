# LLM Orchestrator

A two-part project for batch-processing text files through an LLM: a mock LLM **provider** that simulates different service-health scenarios, and an **orchestrator** that reads files, calls the provider (classify, summarize, extract keywords), and exports the results to Excel.

## Projects

| Project | Description |
|---|---|
| [`provider/`](provider) | FastAPI mock LLM server exposing three simulated endpoints — `Active` (always available), `Partial` (sometimes returns `429`), and `Inactive` (mostly returns `429`/`500`) — used to exercise the orchestrator's concurrency and error-handling logic. |
| [`orchestrator/`](orchestrator) | Batch client that processes text files through a configured LLM provider using multithreading (per file) and asyncio (per operation), then exports results to Excel. |

## Requirements

| Requirement | Version |
|---|---|
| Python | >= 3.14 |
| Poetry | latest |

Each project has its own Poetry environment (`pyproject.toml` + `poetry.lock`) and must be installed/run separately.

## Quick start

1. **Start the provider(s)** — run this first, so the orchestrator has an endpoint to call.
2. **Run the orchestrator** — process files against one of the running providers.

### 1. Run the provider

```bash
cd provider
poetry install
```

The provider reads host/port settings from `provider/.env` (defaults shown):

```ini
UVICORN_HOST=127.0.0.1
FULL_PORT=8000
PARTIAL_PORT=8100
INACTIVE_PORT=8200
```

Start one server, or all three at once:

```bash
poetry run run-full      # Active provider   -> http://127.0.0.1:8000
poetry run run-partial   # Partial provider  -> http://127.0.0.1:8100
poetry run run-inactive  # Inactive provider -> http://127.0.0.1:8200
poetry run run-all       # starts all three together
```

### 2. Run the orchestrator

```bash
cd orchestrator
poetry install
```

Configure the target providers in `orchestrator/src/config/config.ini` (already preconfigured to match the provider's default ports):

```ini
[General]
debug_mode = False
MAX_CONCURRENCY = 3

[LLM Client Active]
host_name = http://127.0.0.1:8000

[LLM Client Partial]
host_name = http://127.0.0.1:8100

[LLM Client Inactive]
host_name = http://127.0.0.1:8200
```

Then run it, selecting which provider to target:

```bash
poetry run orchestrator --client Active [--max-concurrency N]
```

| Flag | Required | Description |
|---|---|---|
| `--client` | ✅ | Preconfigured LLM provider to target: `Active`, `Inactive`, or `Partial` |
| `--max-concurrency` | ❌ | Overrides `MAX_CONCURRENCY` from config |

Results are saved under `~/LLM Orchestrator result/` (`success/` and `failed/` subfolders as timestamped `.xlsx` files), with logs under `orchestrator/log/`.

See each project's own README for more detail: [`provider/README.md`](provider/README.md), [`orchestrator/README.md`](orchestrator/README.md).
