from collections.abc import Callable
from typing import Any

import pytest

from epregistry.epregistry import EntryPointRegistry, available_groups


# Constants for testing
CONSOLE_SCRIPTS = "console_scripts"  # This group exists in most Python installations
NONEXISTENT_GROUP = "nonexistent.group"
NONEXISTENT_NAME = "nonexistent.name"


def test_registry_initialization():
    """Test basic registry initialization."""
    registry = EntryPointRegistry[Any](CONSOLE_SCRIPTS)
    assert registry.group == CONSOLE_SCRIPTS


def test_registry_get_nonexistent_entry_point(
    registry: EntryPointRegistry[Callable[..., Any]],
):
    """Test getting a nonexistent entry point."""
    entry_point = registry.get(NONEXISTENT_NAME)
    assert entry_point is None


def test_registry_getitem_nonexistent(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test __getitem__ with nonexistent entry point."""
    with pytest.raises(KeyError):
        _ = registry[NONEXISTENT_NAME]


def test_registry_iteration(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test iteration over registry."""
    names = list(registry)
    assert isinstance(names, list)
    # At least one entry point should exist in console_scripts
    assert len(names) > 0


def test_registry_length(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test len() operation on registry."""
    # Should have at least one console script
    assert len(registry) > 0


def test_registry_contains(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test contains operation on registry."""
    assert NONEXISTENT_NAME not in registry
    # Get first available name and test it
    if len(registry) > 0:
        first_name = next(iter(registry))
        assert first_name in registry


def test_registry_names(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test getting list of entry point names."""
    names = registry.names()
    assert isinstance(names, list)
    assert len(names) > 0


def test_registry_get_all(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test getting all entry points."""
    all_entry_points = registry.get_all()
    assert isinstance(all_entry_points, dict)
    assert len(all_entry_points) > 0


def test_registry_empty_group():
    """Test registry with empty group."""
    registry = EntryPointRegistry[Any](NONEXISTENT_GROUP)
    assert len(registry) == 0
    assert registry.names() == []


def test_available_groups():
    """Test getting available groups."""
    groups = available_groups()
    assert isinstance(groups, list)
    assert CONSOLE_SCRIPTS in groups


def test_get_metadata(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test getting entry point metadata."""
    if len(registry) > 0:
        name = next(iter(registry)).name
        metadata = registry.get_metadata(name)
        assert isinstance(metadata, dict)
        assert "module" in metadata
        assert "attr" in metadata
        assert "dist" in metadata
        assert "version" in metadata


def test_get_metadata_nonexistent(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test getting metadata for nonexistent entry point."""
    with pytest.raises(ValueError, match=r"No entry point named*"):
        registry.get_metadata(NONEXISTENT_NAME)


def test_generic_typing():
    """Test generic typing functionality."""
    registry = EntryPointRegistry[Callable[..., Any]](CONSOLE_SCRIPTS)
    assert isinstance(registry, EntryPointRegistry)


def test_load_missing_entry_point(registry: EntryPointRegistry[Callable[..., Any]]):
    """Test loading a nonexistent entry point."""
    result = registry.load(NONEXISTENT_NAME)
    assert result is None


@pytest.mark.parametrize(
    ("group", "expected_type"),
    [
        (CONSOLE_SCRIPTS, EntryPointRegistry[Callable[..., Any]]),
        ("pytest11", EntryPointRegistry[Any]),  # pytest plugins group
    ],
)
def test_registry_type_parameters(group: str, expected_type: type):
    """Test registry with different type parameters."""
    registry = expected_type(group)
    assert isinstance(registry, EntryPointRegistry)


def test_load_all_empty_group():
    """Test load_all() with empty group."""
    registry = EntryPointRegistry[Any](NONEXISTENT_GROUP)
    assert registry.load_all() == {}


def test_multiple_registries_same_cache():
    """Test that multiple registries share the same cache."""
    registry1 = EntryPointRegistry[Any](CONSOLE_SCRIPTS)
    registry2 = EntryPointRegistry[Any](CONSOLE_SCRIPTS)
    assert registry1._get_cache() is registry2._get_cache()


def test_unknown_group_does_not_create_phantom_group():
    from epregistry import available_groups, filter_entry_points

    registry = EntryPointRegistry[Any]("no.such.group.phantom")
    assert len(registry) == 0
    assert registry.names() == []
    assert "no.such.group.phantom" not in available_groups()
    assert "no.such.group.phantom" not in filter_entry_points(group="no.such.*")


def test_get_all_returns_copy():
    registry = EntryPointRegistry[Any](CONSOLE_SCRIPTS)
    eps = registry.get_all()
    eps["BOGUS"] = None  # ty: ignore[invalid-assignment]
    assert "BOGUS" not in registry.get_all()
    assert "BOGUS" not in EntryPointRegistry[Any](CONSOLE_SCRIPTS)


def test_clear_entry_point_cache_refreshes_registries(monkeypatch: pytest.MonkeyPatch):
    from importlib.metadata import EntryPoint

    from epregistry import clear_entry_point_cache, epregistry as mod

    registry = EntryPointRegistry[Any]("epregistry.test.refresh")
    assert len(registry) == 0
    ep = EntryPoint(name="late", value="os:getcwd", group="epregistry.test.refresh")
    monkeypatch.setattr(mod, "entry_points", lambda: [ep])
    clear_entry_point_cache()
    try:
        assert registry.names() == ["late"]
        assert "epregistry.test.refresh" in mod.available_groups()
    finally:
        monkeypatch.undo()
        clear_entry_point_cache()
    assert len(registry) == 0


def test_cache_initialized_once_across_threads(monkeypatch: pytest.MonkeyPatch):
    import threading
    import time

    from epregistry import clear_entry_point_cache, epregistry as mod

    calls = 0

    def slow_entry_points():
        nonlocal calls
        calls += 1
        time.sleep(0.05)
        return []

    monkeypatch.setattr(mod, "entry_points", slow_entry_points)
    clear_entry_point_cache()
    results: list[object] = []
    try:
        threads = [
            threading.Thread(target=lambda: results.append(mod._get_entry_point_cache()))
            for _ in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert calls == 1
        assert all(r is results[0] for r in results)
    finally:
        monkeypatch.undo()
        clear_entry_point_cache()


def test_same_name_keeps_first_entry_point(monkeypatch: pytest.MonkeyPatch):
    from importlib.metadata import EntryPoint

    from epregistry import clear_entry_point_cache, epregistry as mod

    first = EntryPoint(name="dup", value="os:getcwd", group="epregistry.test.dup")
    second = EntryPoint(name="dup", value="os:getpid", group="epregistry.test.dup")
    monkeypatch.setattr(mod, "entry_points", lambda: [first, second])
    clear_entry_point_cache()
    try:
        assert EntryPointRegistry[Any]("epregistry.test.dup")["dup"] is first
    finally:
        monkeypatch.undo()
        clear_entry_point_cache()
