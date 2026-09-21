# LLM Orchestrator

Batch-process text files through an LLM — classify, summarize, and extract keywords — and export the results to Excel.

## How it works

- **Multithreaded by file** — each file is processed in its own worker thread, with concurrency capped by a semaphore (`MAX_CONCURRENCY`).
- **Async per file** — within a thread, the three LLM operations (classify, summarize, keyword extraction) run concurrently via `asyncio.gather`, so I/O-bound HTTP calls don't block each other.

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

Edit `src/config/config.ini`:

```ini
[General]
debug_mode = False
MAX_CONCURRENCY = 3

[LLM Client Active]
host_name = http://127.0.0.1:8000
...
```

Three LLM providers are preconfigured, one `[LLM Client <name>]` section each with its own `host_name`:

- `Active`
- `Inactive`
- `Partial`

Only one provider is selected per orchestrator run, via `--client`.

##  Usage

```bash
poetry run orchestrator --client Active [--max-concurrency N]
```

| Flag | Required | Description |
|---|---|---|
| `--client` | ✅ | Preconfigured LLM provider to target: `Active`, `Inactive`, or `Partial` |
| `--max-concurrency` | ❌ | Overrides `MAX_CONCURRENCY` from config |

## 📤 Output

Results are saved under `~/LLM Orchestrator result/`:

- `success/processing_success_<timestamp>.xlsx`
- `failed/processing_error_<timestamp>.xlsx`

Logs are saved under `log/`.

## Testing

```bash
poetry run test
```

Extra pytest args are forwarded, e.g. `poetry run test -k llm_client`.
