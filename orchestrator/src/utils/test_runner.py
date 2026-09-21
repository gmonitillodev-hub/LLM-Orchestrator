import sys

import pytest


def run() -> None:
    """Entry point for `poetry run test`, forwarding any extra args to pytest."""
    sys.exit(pytest.main(sys.argv[1:] or ["-v"]))
