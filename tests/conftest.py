"""Pytest fixtures for `strategies/`."""
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_dir() -> Path:
    """Absolute path to the repository directory."""
    return Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="session", autouse=True)
def load_plugins() -> None:
    """Load plugins."""
    from oteapi.plugins.plugins import load_plugins

    load_plugins()
