# Orchestrator documentation

## Overview

The orchestrator collects user requests pointing to files/folders, runs three LLM
inference operations (classify, summarize, keyword extraction) per file, and publishes
an Excel report of successes/failures. Processing is concurrent: one thread per file,
and one `asyncio` task per operation within each file.

## Phases

| # | Phase | Summary |
|---|-------|---------|
| 1 | Initialization | Load config, create the `LlmClient`, set up logging. |
| 2 | Request collection | Prompt the user for requests, resolve them into a flat file list. |
| 3 | Process requests | Process every file concurrently (thread + async per operation). |
| 4 | Publish results | Write success/error Excel reports. |

### 1. Initialization

`Orchestrator(client, max_concurrency=None)`:
- Reads `config.ini` and resolves `MAX_CONCURRENCY` (overridden by `max_concurrency` if provided).
- Instantiates `LlmClient` for the selected provider (`Active`/`Inactive`/`Partial`, matching the `[LLM Client <name>]` section).
- Sets up the logger (console output enabled when `debug_mode` is true).

### 2. Request collection

`initialize_request_processor()`:
- Repeatedly prompts the user (`accept_new_request()` / `ask_new_request()`) for one or more requests, each pointing to a file or folder.
- Flattens the resulting `ProcessedPath` entries (one per file) into `self.file_to_process`.
- Clears the terminal and logs the collected file count.

See [Request model](#request-model) for how a request resolves its path into files.

### 3. Process requests

`process_requests()` processes all files concurrently, bounding concurrency with a semaphore.

See [Concurrency model](#concurrency-model) for the full thread/semaphore/async mechanics.

### 4. Publish results

`publish_processing_result()`:
- Splits `file_to_process` into failed/successful files based on `processing_results.is_failed`.
- Writes two timestamped Excel reports under `~/LLM Orchestrator result/`:
  - `failed/processing_error_<timestamp>.xlsx` — file name, path, error status code and detail.
  - `success/processing_success_<timestamp>.xlsx` — file name and path.
- Logs the counts for both outputs.

## Request model

Each request is a `Request` pydantic `BaseModel` (`classes/request.py`) with:

- `request_id`: a generated `UUID`.
- `file_path`: the raw path (file or folder) provided by the user.
- `file_data`: the list of `ProcessedPath` entries resolved from `file_path` (empty until validated).
- `operation_type`: optional `OperationEnum` value.

A `model_validator(mode="after")` calls `check_folder(file_path)` right after the model is built:

- **File** → returns a single `ProcessedPath` for that file.
- **Folder** → returns one `ProcessedPath` per file directly inside it (no recursion into subfolders).

Each `ProcessedPath` is appended to `file_data`, so a validated `Request` always exposes the
flat list of files to process. Exceptions raised while checking the path (e.g. invalid path)
are caught and logged, leaving `file_data` empty for that request.

## Concurrency model

Processing has two nested levels of concurrency:

1. **Across files** — one OS thread per file, capped by a semaphore.
2. **Within a file** — one `asyncio` task per LLM operation, run concurrently on that thread.

### Across files: thread pool + semaphore

`process_requests()`:
1. Creates one `threading.Semaphore(MAX_CONCURRENCY)` shared by all workers.
2. Spawns one `threading.Thread` per file (named `Th-<file_name>`) and starts all of them immediately.
3. Joins all threads before returning, so the phase completes only once every file is done.

Each thread runs `_process_file_sync(file, semaphore)`:
- Acquires the shared `semaphore` (`with semaphore:`) — only up to `MAX_CONCURRENCY` threads can hold
  it at once, so the rest simply block until a slot frees up, even though every thread already started.
- Once acquired, runs `asyncio.run(process_file(file))` — each thread needs its own event loop, since
  asyncio loops aren't shared across threads.

### Within a file: async operations

`process_file(file)` reads the file content and awaits `inference_request(content)`, which:
1. For each `OperationEnum` value (`CLASSIFY`, `SUMMARIZE`, `KEYWORD_EXTRACTION`), builds the
   operation-specific prompt and creates a `self.llm_client.call_llm(...)` coroutine.
2. Collects all coroutines into a `promises` list (not yet awaited).
3. Awaits them together with `await asyncio.gather(*promises)`, so the three LLM calls run
   concurrently instead of sequentially. Any exception raised during gathering is caught and logged.

Back in `process_file`, each result is inspected and used to build the file's `ProcessingResult`:
- **Failure** → appends an `Error` (detail + status code) and sets `is_failed = True`.
- **Success** → appends the response text.

A `print_lock` (`threading.Lock`) guards the final per-file completion `print(...)` so concurrent
threads don't interleave console output.

## Implementation decisions

**Multithreading (not multiprocessing) across files.**
File processing is I/O-bound (waiting on REST calls to the LLM provider), not CPU-bound. Python's GIL
is released while a thread waits on network I/O, so a single process can serve many concurrent LLM
calls without the memory/startup overhead of separate OS processes — which would bring no benefit here
since there's no CPU-intensive work to parallelize across cores.

**Asyncio (not more threads) within a file.**
The three per-file operations use `asyncio.gather` instead of one thread per operation, to keep the
system scalable as the number of concurrent I/O operations grows. Coroutines are far cheaper than OS
threads (no per-thread memory/scheduling overhead), so a single thread's event loop can juggle many
concurrent awaited calls with a much smaller resource footprint.
