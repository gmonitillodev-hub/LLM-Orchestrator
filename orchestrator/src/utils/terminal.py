import configparser
import os
from pathlib import Path


def _running_in_notebook() -> bool:
    """Detect Jupyter/Colab, including when this code runs as a subprocess spawned by
    Colab's `!` shell magic (e.g. `!poetry run orchestrator ...`), which inherits the
    parent's environment variables but is not itself connected to the IPython kernel."""
    if any(key.startswith("COLAB_") for key in os.environ):
        return True
    if "JPY_PARENT_PID" in os.environ:
        return True
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ImportError:
        return False


def clear_terminal():
    if _running_in_notebook():
        # A real screen clear isn't achievable here: notebook cell output (especially
        # for shell/`!` commands) is streamed as plain text, not rendered by a real
        # terminal that understands clear-screen ANSI sequences. Use a visual
        # separator instead of a no-op so the user still gets a clear break.
        print("\n" * 3 + "-" * 60)
    else:
        os.system("cls" if os.name == "nt" else "clear")


def print_info():
    print("\n ------------------------------------------------------- ")
    print(" ------------------ LLM Orchestrator -------------------")
    print(" ----- Process your document in few simple steps -------")
    print(" - Insert the path of one or more documents or folders -")
    print(" ------------------------------------------------------- ")


def to_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes", "y")


def get_config():
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(src_dir, "config", "config.ini")

    config = configparser.ConfigParser()
    if not config.read(filenames=config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    return config


def get_repository_root() -> Path:
    """Root of the LLM-Orchestrator repository (parent of the `orchestrator` project folder),
    used to store run outputs (e.g. processing results) inside the repo instead of the user's home."""
    # this file: <repo>/orchestrator/src/utils/terminal.py
    return Path(__file__).resolve().parents[3]
