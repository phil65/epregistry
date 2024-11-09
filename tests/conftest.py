from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from epregistry.epregistry import EntryPointRegistry


CONSOLE_SCRIPTS = "console_scripts"  # This group exists in most Python installations


@pytest.fixture
def registry() -> EntryPointRegistry[Callable[..., Any]]:
    """Create a registry using console_scripts group."""
    return EntryPointRegistry[Callable[..., Any]](CONSOLE_SCRIPTS)
