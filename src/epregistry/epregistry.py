"""Module for managing entry points through a registry system."""

from __future__ import annotations

from collections import defaultdict
from functools import cache
from importlib.metadata import EntryPoint, entry_points
import logging
import pathlib
from typing import TYPE_CHECKING, Any, Generic

from typing_extensions import TypeVar


if TYPE_CHECKING:
    from collections.abc import Iterator


T = TypeVar("T", default=Any)

# Global cache for ALL entry points across all groups
_entry_point_cache: dict[str, dict[str, EntryPoint]] | None = None
logger = logging.getLogger(__name__)


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


def get_all_entry_points() -> list[EntryPoint]:
    """Get all available entry points across all groups.

    Returns:
        A nested dictionary with the structure:
        {group_name: {entry_point_name: entry_point}}

    Example:
        >>> all_eps = get_all_entry_points()
        >>> console_scripts = all_eps.get('console_scripts', {})
        >>> for name, ep in console_scripts.items():
        ...     print(f"{name}: {ep.module}:{ep.attr}")
    """
    cache = EntryPointRegistry._get_cache()
    return [ep for group_eps in cache.values() for ep in group_eps.values()]


class ModuleEntryPointRegistry(Generic[T]):
    """A registry for managing entry points organized by their module names.

    This class provides an interface to work with entry points grouped by their
    source modules. It shares the same global cache as EntryPointRegistry but
    presents a different view of the data.

    Attributes:
        module: The module name to filter entry points by.
    """

    def __init__(self, module: str | None = None):
        """Initialize the registry for a specific module.

        Args:
            module: The module name to manage entry points for.
        """
        self.module = module
        self._cache: dict[str, list[EntryPoint]] | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.module!r})"

    @property
    def cache(self) -> dict[str, list[EntryPoint]]:
        """Get the module-specific cache of entry points."""
        if self._cache is None:
            self._build_cache()
        assert self._cache is not None
        return self._cache

    def _build_cache(self) -> None:
        """Build the module-specific cache from the global entry point cache."""
        result: defaultdict[str, list[EntryPoint]] = defaultdict(list)
        global_cache = self._get_cache()

        # If no module specified, don't filter
        if self.module is None:
            for group_eps in global_cache.values():
                for ep in group_eps.values():
                    result[ep.group].append(ep)
        else:
            module_with_dot = f"{self.module}."
            for group_eps in global_cache.values():
                for ep in group_eps.values():
                    if ep.module == self.module or ep.module.startswith(module_with_dot):
                        result[ep.group].append(ep)

        self._cache = dict(result)

    @staticmethod
    def _get_cache() -> dict[str, dict[str, EntryPoint]]:
        """Get or initialize the global entry point cache."""
        global _entry_point_cache
        if _entry_point_cache is None:
            _entry_point_cache = _initialize_cache()
        return _entry_point_cache

    def groups(self) -> list[str]:
        """Get all groups that contain entry points from this module."""
        return list(self.cache.keys())

    def get_group(self, group: str) -> list[EntryPoint]:
        """Get all entry points for a specific group from this module.

        Args:
            group: The entry point group name.

        Returns:
            List of entry points in the specified group.
        """
        return self.cache.get(group, [])

    def load_group(self, group: str) -> list[T]:
        """Load all entry points for a specific group from this module.

        Args:
            group: The entry point group name.

        Returns:
            List of loaded entry points.
        """
        return [ep.load() for ep in self.get_group(group)]

    def __iter__(self) -> Iterator[tuple[str, list[EntryPoint]]]:
        """Iterate over groups and their entry points."""
        return iter(self.cache.items())

    def __len__(self) -> int:
        """Get the total number of entry points across all groups."""
        return sum(len(eps) for eps in self.cache.values())

    def __contains__(self, group: str) -> bool:
        """Check if the module has entry points in a specific group."""
        return group in self.cache

    def get_all(self) -> dict[str, list[EntryPoint]]:
        """Get all entry points organized by group."""
        return self.cache

    def load_all(self) -> dict[str, list[T]]:
        """Load all entry points, organized by group."""
        return {group: [ep.load() for ep in eps] for group, eps in self.cache.items()}


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
        # Initialize instance cache
        self._cache: dict[str, EntryPoint] | None = None
        # Ensure the group exists in the global cache
        if self.group not in self._get_cache():
            self._get_cache()[self.group] = {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.group!r})"

    @property
    def cache(self) -> dict[str, EntryPoint]:
        """Get the instance cache of entry points.

        Returns:
            dict: Mapping of entry point names to EntryPoint objects.
        """
        if self._cache is None:
            self._cache = self._get_cache()[self.group]
        return self._cache

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
        return self.cache.get(name)

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
            return self.cache[name]
        except KeyError as e:
            msg = f"No entry point named {name!r} found in group {self.group!r}"
            raise KeyError(msg) from e

    def __iter__(self) -> Iterator[EntryPoint]:
        """Iterate over entry point names.

        Returns:
            Iterator of entry point names.
        """
        return iter(self.cache.values())

    def __len__(self) -> int:
        """Get the number of available entry points.

        Returns:
            The number of entry points in this registry.
        """
        return len(self.cache)

    def __contains__(self, ep: str | EntryPoint) -> bool:
        """Check if an entry point name exists.

        Args:
            ep: The name / EntryPoint object to check.

        Returns:
            True if the entry point exists, False otherwise.
        """
        if isinstance(ep, str):
            return ep in self.cache
        return ep in self.cache.values()

    def names(self) -> list[str]:
        """Get a list of all available entry point names.

        Returns:
            List of entry point names.
        """
        return list(self.cache.keys())

    def get_all(self) -> dict[str, EntryPoint]:
        """Get all entry points as a dictionary.

        Returns:
            Dictionary mapping entry point names to entry points.
        """
        return self.cache

    def load_all(self) -> dict[str, T]:
        """Load all entry points.

        Returns:
            Dictionary mapping entry point names to loaded entry points.
            Any entry points that fail to load will not be included in the result.
        """
        result = {}
        for name, ep in self.get_all().items():
            try:
                loaded = ep.load()
                result[name] = loaded
            except Exception as e:  # noqa: BLE001
                msg = "Failed to load entry point %r from group %r: %s"
                logger.warning(msg, name, self.group, str(e))
        return result

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

    def get_extension_point_dir(self, name: str) -> pathlib.Path:
        """Return the directory of an installed extension point object by name."""
        ep = self.load(name)
        assert ep
        assert hasattr(ep, "__file__")
        path = pathlib.Path(ep.__file__).resolve()
        return path.parent


def available_groups() -> list[str]:
    """Get a list of all available entry point groups.

    Returns:
        List of entry point group names.
    """
    return list(EntryPointRegistry._get_cache().keys())


def filter_entry_points(
    group: str | None = None,
    distribution: str | None = None,
    name_pattern: str | None = None,
) -> dict[str, dict[str, EntryPoint]]:
    """Filter entry points based on specified criteria.

    Args:
        group: Optional group name to filter by
        distribution: Optional distribution name to filter by
        name_pattern: Optional string pattern to match against entry point names
            (supports simple wildcards: * and ?)

    Returns:
        Filtered dictionary of entry points maintaining the same structure as the cache
    """
    cache = EntryPointRegistry._get_cache()
    result: dict[str, dict[str, EntryPoint]] = {}

    def match_pattern(text: str, pattern: str) -> bool:
        """Simple pattern matching supporting * and ? wildcards."""
        import fnmatch

        return fnmatch.fnmatch(text.lower(), pattern.lower())

    for group_name, group_eps in cache.items():
        # Filter by group if specified
        if group and not match_pattern(group_name, group):
            continue

        filtered_eps = {}
        for ep_name, ep in group_eps.items():
            # Filter by distribution if specified
            if distribution and not (
                ep.dist and match_pattern(ep.dist.metadata["Name"], distribution)
            ):
                continue

            # Filter by name pattern if specified
            if name_pattern and not match_pattern(ep_name, name_pattern):
                continue

            filtered_eps[ep_name] = ep

        if filtered_eps:
            result[group_name] = filtered_eps

    return result


def search_entry_points(
    query: str,
    include_groups: bool = True,
    include_names: bool = True,
    include_distributions: bool = True,
) -> dict[str, dict[str, EntryPoint]]:
    """Search entry points using a general query string.

    Args:
        query: Search string to match against entry points
        include_groups: Whether to search in group names
        include_names: Whether to search in entry point names
        include_distributions: Whether to search in distribution names

    Returns:
        Dictionary of matching entry points
    """
    cache = EntryPointRegistry._get_cache()
    result: dict[str, dict[str, EntryPoint]] = {}
    query = query.lower()

    for group_name, group_eps in cache.items():
        matching_eps = {}

        # Check group name
        group_matches = include_groups and query in group_name.lower()

        for ep_name, ep in group_eps.items():
            matches = False

            # Check entry point name
            if include_names and query in ep_name.lower():
                matches = True

            # Check distribution name
            if (
                include_distributions
                and ep.dist
                and query in ep.dist.metadata["Name"].lower()
            ):
                matches = True

            if matches or group_matches:
                matching_eps[ep_name] = ep

        if matching_eps:
            result[group_name] = matching_eps

    return result


def list_distributions() -> set[str]:
    """Get a set of all unique distribution names that provide entry points.

    Returns:
        Set of distribution names
    """
    distributions = set()
    cache = EntryPointRegistry._get_cache()

    for group_eps in cache.values():
        for ep in group_eps.values():
            if ep.dist:
                distributions.add(ep.dist.metadata["Name"])

    return distributions


if __name__ == "__main__":
    # Create a registry for console scripts
    registry = ModuleEntryPointRegistry("pytest")
    print(registry.get_all())
