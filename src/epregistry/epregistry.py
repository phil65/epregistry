"""Module for managing entry points through a registry system."""

from collections import defaultdict
from collections.abc import Callable, Iterator
from functools import cache
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Generic, TypeVar


T = TypeVar("T")

# Global cache for ALL entry points across all groups
_entry_point_cache: dict[str, dict[str, EntryPoint]] | None = None


@cache
def _initialize_cache() -> dict[str, dict[str, EntryPoint]]:
    """Initialize the global cache with ALL entry points.

    Returns:
        dict: A nested dictionary mapping group names to their entry points.
            Structure: {group_name: {entry_point_name: entry_point}}
    """
    all_entry_points: defaultdict[str, dict[str, Any]] = defaultdict(dict)
    for ep in entry_points():
        all_entry_points[ep.group][ep.name] = ep
    return dict(all_entry_points)


class EntryPointRegistry(Generic[T]):
    """A registry for managing and accessing entry points of a specific group.

    This class provides a convenient interface to work with entry points from a specified
    group. It handles caching and provides various methods to access / load entry points.

    Args:
        group: The entry point group to manage.

    Attributes:
        group: The name of the entry point group being managed.
    """

    def __init__(self, group: str):
        """Initialize the registry for a specific entry point group.

        Args:
            group: The entry point group to manage.
        """
        self.group = group
        # Ensure the group exists in the cache
        if self.group not in self._get_cache():
            self._get_cache()[self.group] = {}

    @staticmethod
    def _get_cache() -> dict[str, dict[str, EntryPoint]]:
        """Get or initialize the global entry point cache.

        Returns:
            dict: The global cache of entry points.
        """
        global _entry_point_cache
        if _entry_point_cache is None:
            _entry_point_cache = _initialize_cache()
        return _entry_point_cache

    def get(self, name: str) -> EntryPoint | None:
        """Get an entry point by name.

        Args:
            name: The name of the entry point.

        Returns:
            The entry point if found, None otherwise.
        """
        return self._get_cache()[self.group].get(name)

    def load(self, name: str) -> T | None:
        """Load an entry point by name.

        Args:
            name: The name of the entry point to load.

        Returns:
            The loaded entry point if found, None otherwise.
        """
        entry_point = self.get(name)
        return entry_point.load() if entry_point is not None else None

    def __getitem__(self, name: str) -> EntryPoint:
        """Get an entry point by name.

        Args:
            name: The name of the entry point.

        Returns:
            The requested entry point.

        Raises:
            KeyError: If the entry point is not found.
        """
        try:
            return self._get_cache()[self.group][name]
        except KeyError as e:
            msg = f"No entry point named {name!r} found in group {self.group!r}"
            raise KeyError(msg) from e

    def __iter__(self) -> Iterator[str]:
        """Iterate over entry point names.

        Returns:
            Iterator of entry point names.
        """
        return iter(self._get_cache()[self.group])

    def __len__(self) -> int:
        """Get the number of available entry points.

        Returns:
            The number of entry points in this registry.
        """
        return len(self._get_cache()[self.group])

    def __contains__(self, name: str) -> bool:
        """Check if an entry point name exists.

        Args:
            name: The name to check.

        Returns:
            True if the entry point exists, False otherwise.
        """
        return name in self._get_cache()[self.group]

    def names(self) -> list[str]:
        """Get a list of all available entry point names.

        Returns:
            List of entry point names.
        """
        return list(self._get_cache()[self.group].keys())

    def get_all(self) -> dict[str, EntryPoint]:
        """Get all entry points as a dictionary.

        Returns:
            Dictionary mapping entry point names to entry points.
        """
        return self._get_cache()[self.group]

    def load_all(self) -> dict[str, T]:
        """Load all entry points.

        Returns:
            Dictionary mapping entry point names to loaded entry points.
        """
        return {name: ep.load() for name, ep in self.get_all().items()}

    def get_metadata(self, name: str) -> dict[str, Any]:
        """Get detailed metadata for an entry point."""
        ep = self.get(name)
        if not ep:
            msg = f"No entry point named '{name}' found in group '{self.group}'"
            raise ValueError(msg)
        return {
            "module": ep.module,
            "attr": ep.attr,
            "dist": ep.dist.metadata["Name"] if ep.dist else None,
            "version": ep.dist.version if ep.dist else None,
        }


def available_groups() -> list[str]:
    """Get a list of all available entry point groups.

    Returns:
        List of entry point group names.
    """
    return list(EntryPointRegistry._get_cache().keys())


if __name__ == "__main__":
    # Create a registry for console scripts
    registry = EntryPointRegistry[Callable]("console_scripts")

    # Print available console scripts
    print("Available console scripts:")
    for name in registry.names():
        print(f"- {name}")

    print(f"\nTotal scripts: {len(registry)}")
