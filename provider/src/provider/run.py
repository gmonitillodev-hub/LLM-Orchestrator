import os
import subprocess
import sys
import time
from pathlib import Path

import uvicorn

from provider import inactive


def _load_env_file() -> None:
    root_env = Path(__file__).resolve().parents[2] / ".env"
    if not root_env.exists():
        return

    for line in root_env.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
            continue
        key, value = cleaned.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def run_full() -> None:
    _load_env_file()
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("FULL_PORT", "8000"))
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("provider:full", host=host, port=port, reload=reload_enabled)


def run_partial() -> None:
    _load_env_file()
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("PARTIAL_PORT", "8100"))
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("provider:partial", host=host, port=port, reload=reload_enabled)

def run_inactive() -> None:
    _load_env_file()
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("INACTIVE_PORT", "8200"))
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("provider:inactive", host=host, port=port, reload=reload_enabled)


def run_all() -> None:
    _load_env_file()
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    full_port = os.getenv("FULL_PORT", "8000")
    partial_port = os.getenv("PARTIAL_PORT", "8100")
    inactive_port = os.getenv("INACTIVE_PORT", "8200")
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").lower() in {"1", "true", "yes", "on"}

    base_cmd = [sys.executable, "-m", "uvicorn"]
    full_cmd = base_cmd + ["provider:full", "--host", host, "--port", str(full_port)]
    partial_cmd = base_cmd + ["provider:partial", "--host", host, "--port", str(partial_port)]
    inactive_cmd = base_cmd + ["provider:inactive", "--host", host, "--port", str(inactive_port)]
    if reload_enabled:
        full_cmd.append("--reload")
        partial_cmd.append("--reload")
        inactive_cmd.append("--reload")

    full_proc = subprocess.Popen(full_cmd)
    partial_proc = subprocess.Popen(partial_cmd)
    inactive_proc = subprocess.Popen(inactive_cmd)

    try:
        while True:
            full_code = full_proc.poll()
            partial_code = partial_proc.poll()
            inactive_code = inactive_proc.poll()
            if full_code is not None or partial_code is not None or inactive_code is not None:
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (full_proc, partial_proc, inactive_proc):
            if proc.poll() is None:
                proc.terminate()
        for proc in (full_proc, partial_proc, inactive_proc):
            if proc.poll() is None:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
