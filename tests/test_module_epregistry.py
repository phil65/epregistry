"""Tests for the ModuleEntryPointRegistry class."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from epregistry.epregistry import ModuleEntryPointRegistry


# Test constants
PYTEST_MODULE = "pytest"  # pytest has multiple entry points in different groups
NONEXISTENT_MODULE = "nonexistent.module"
NONEXISTENT_GROUP = "nonexistent.group"


@pytest.fixture
def registry() -> ModuleEntryPointRegistry[Any]:
    """Fixture providing a ModuleEntryPointRegistry instance."""
    return ModuleEntryPointRegistry[Any](PYTEST_MODULE)


def test_registry_initialization():
    """Test basic registry initialization."""
    registry = ModuleEntryPointRegistry[Any](PYTEST_MODULE)
    assert registry.module == PYTEST_MODULE


def test_registry_empty_module():
    """Test registry with nonexistent module."""
    registry = ModuleEntryPointRegistry[Any](NONEXISTENT_MODULE)
    assert len(registry) == 0
    assert registry.groups() == []


def test_registry_groups(registry: ModuleEntryPointRegistry[Any]):
    """Test getting groups for a module."""
    groups = registry.groups()
    assert isinstance(groups, list)
    assert len(groups) > 0
    # pytest should have entry points in 'pytest11' group
    assert "console_scripts" in groups


def test_registry_get_group(registry: ModuleEntryPointRegistry[Any]):
    """Test getting entry points for a specific group."""
    # Get entry points for pytest11 group
    eps = registry.get_group("console_scripts")
    assert isinstance(eps, list)
    assert len(eps) > 0


def test_registry_get_nonexistent_group(registry: ModuleEntryPointRegistry[Any]):
    """Test getting entry points for a nonexistent group."""
    eps = registry.get_group(NONEXISTENT_GROUP)
    assert eps == []


def test_registry_iteration(registry: ModuleEntryPointRegistry[Any]):
    """Test iteration over registry."""
    items = list(registry)
    assert isinstance(items, list)
    assert len(items) > 0
    # Each item should be a tuple of (group_name, entry_points)
    assert isinstance(items[0], tuple)
    assert len(items[0]) == 2  # noqa: PLR2004
    assert isinstance(items[0][1], list)


def test_registry_length(registry: ModuleEntryPointRegistry[Any]):
    """Test len() operation on registry."""
    assert len(registry) > 0


def test_registry_contains(registry: ModuleEntryPointRegistry[Any]):
    """Test contains operation on registry."""
    assert NONEXISTENT_GROUP not in registry
    assert "console_scripts" in registry


def test_registry_get_all(registry: ModuleEntryPointRegistry[Any]):
    """Test getting all entry points."""
    all_entry_points = registry.get_all()
    assert isinstance(all_entry_points, dict)
    assert len(all_entry_points) > 0
    # Values should be lists of entry points
    first_group = next(iter(all_entry_points.values()))
    assert isinstance(first_group, list)


def test_load_group(registry: ModuleEntryPointRegistry[Any]):
    """Test loading entry points for a group."""
    loaded = registry.load_group("console_scripts")
    assert isinstance(loaded, list)
    assert len(loaded) > 0
    # Loaded objects should be the actual implementations
    assert all(callable(obj) for obj in loaded)


def test_load_nonexistent_group(registry: ModuleEntryPointRegistry[Any]):
    """Test loading entry points for a nonexistent group."""
    loaded = registry.load_group(NONEXISTENT_GROUP)
    assert loaded == []


def test_load_all(registry: ModuleEntryPointRegistry[Any]):
    """Test loading all entry points."""
    loaded = registry.load_all()
    assert isinstance(loaded, dict)
    assert len(loaded) > 0
    # Each value should be a list of loaded entry points
    first_group = next(iter(loaded.values()))
    assert isinstance(first_group, list)


def test_generic_typing():
    """Test generic typing functionality."""
    registry = ModuleEntryPointRegistry[Callable[..., Any]](PYTEST_MODULE)
    assert isinstance(registry, ModuleEntryPointRegistry)


def test_multiple_registries_same_cache():
    """Test that multiple registries share the same cache."""
    registry1 = ModuleEntryPointRegistry[Any](PYTEST_MODULE)
    registry2 = ModuleEntryPointRegistry[Any](PYTEST_MODULE)
    assert registry1._get_cache() is registry2._get_cache()


def test_cache_building():
    """Test that cache is built correctly."""
    registry = ModuleEntryPointRegistry[Any](PYTEST_MODULE)
    # Access cache to trigger building
    cache = registry.cache
    assert cache is registry._cache
    # Accessing again should use the same cache
    assert registry.cache is cache


@pytest.mark.parametrize(
    ("module", "expected_type"),
    [
        (PYTEST_MODULE, ModuleEntryPointRegistry[Callable[..., Any]]),
        ("setuptools", ModuleEntryPointRegistry[Any]),
    ],
)
def test_registry_type_parameters(module: str, expected_type: type):
    """Test registry with different type parameters."""
    registry = expected_type(module)
    assert isinstance(registry, ModuleEntryPointRegistry)


def test_basic_module_registry():
    """Test basic ModuleEntryPointRegistry functionality using pytest entry points."""
    # Test with pytest module
    registry = ModuleEntryPointRegistry[Any]("pytest")

    # Should find some entry points
    assert len(registry) > 0
    assert "console_scripts" in registry.groups()

    # Test with non-existent module
    empty_registry = ModuleEntryPointRegistry[Any]("nonexistent_module")
    assert len(empty_registry) == 0
    assert empty_registry.groups() == []


def test_module_registry_behavior():
    """Test ModuleEntryPointRegistry with pytest as an example."""
    # Test exact module match
    registry = ModuleEntryPointRegistry[Any]("pytest")
    all_eps = registry.get_all()

    # Should find pytest console scripts
    assert "console_scripts" in all_eps
    assert any(ep.module == "pytest" for ep in all_eps["console_scripts"])

    # Test with plugin module
    plugin_registry = ModuleEntryPointRegistry[Any]("pytest_cov.plugin")
    plugin_eps = plugin_registry.get_all()

    # Should find pytest_cov plugin
    assert "pytest11" in plugin_eps
    assert any(ep.module == "pytest_cov.plugin" for ep in plugin_eps["pytest11"])
