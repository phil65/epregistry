from __future__ import annotations

from functools import cache, lru_cache
from importlib.metadata import distributions, packages_distributions
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, overload

from epregistry.epregistry import clear_entry_point_cache


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from importlib.metadata import Distribution


def _editable_packages(dist: Distribution) -> set[str]:
    """Guess the top-level packages of a .pth-based editable install.

    Editable installs from some build backends (e.g. uv_build) only ship a `.pth`
    file pointing to the source directory, so `packages_distributions()` finds no
    top-level names for them. This checks whether the normalized distribution name
    exists as a package or module in one of the directories listed in those
    `.pth` files.

    Args:
        dist: The distribution to inspect

    Returns:
        The set of top-level package names found (empty or a single name)
    """
    name = dist.metadata.get("Name")
    if not name:
        return set()
    candidate = name.lower().replace("-", "_").replace(".", "_")
    for file in dist.files or []:
        if file.suffix != ".pth":
            continue
        try:
            content = file.read_text()
        except OSError, UnicodeDecodeError:
            continue
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", "import ", "import\t")):
                continue
            directory = Path(line)
            if (directory / candidate / "__init__.py").is_file() or (
                directory / f"{candidate}.py"
            ).is_file():
                return {candidate}
    return set()


def _normalize(name: str) -> str:
    """Normalize a package or distribution name for matching (not for importing)."""
    return name.lower().replace("-", "_").replace(".", "_").lstrip("_")


def _primary_package(distribution_name: str, packages: Iterable[str]) -> str | None:
    """Pick the primary top-level package of a distribution, deterministically.

    Prefers the package whose normalized name equals the normalized distribution
    name; otherwise names without a leading underscore, then the shortest, then
    alphabetical order. Returns the real (importable) name.
    """
    candidates = sorted(packages, key=lambda p: (p.startswith("_"), len(p), p))
    if not candidates:
        return None
    target = _normalize(distribution_name)
    return next((p for p in candidates if _normalize(p) == target), candidates[0])


@cache
def get_packages_distributions() -> Mapping[str, Sequence[str]]:
    """Cached call for packages_distributions (read-only).

    Extends the stdlib mapping with packages of .pth-based editable installs
    which `packages_distributions()` does not report.
    """
    mapping = {pkg: list(dists) for pkg, dists in packages_distributions().items()}
    known = {dist for dists in mapping.values() for dist in dists}
    for dist in distributions():
        name = dist.metadata.get("Name")
        if not name or name in known:
            continue
        for pkg in _editable_packages(dist):
            mapping.setdefault(pkg, []).append(name)
    return MappingProxyType({pkg: tuple(dists) for pkg, dists in mapping.items()})


@cache
def _get_normalized_pkg_dist_map() -> dict[str, str]:
    """Cache the normalized package to distribution mapping.

    Returns:
        A dictionary mapping normalized package names to their distribution names.
    """
    result: dict[str, str] = {}
    for pkg, dists in get_packages_distributions().items():
        # Handle both prefixed and unprefixed package names
        normalized_pkg = pkg.lower().replace("-", "_")
        # Remove leading underscore if present for mapping
        clean_pkg = normalized_pkg.lstrip("_")
        result[normalized_pkg] = dists[0]  # Keep original mapping
        if clean_pkg != normalized_pkg:
            result[clean_pkg] = dists[0]  # Add mapping without underscore
    return result


@cache
def _get_normalized_dist_pkg_map() -> Mapping[str, frozenset[str]]:
    """Cache the normalized distribution to package mapping.

    Returns:
        A mapping of normalized distribution names to their (real) package names.
    """
    result: dict[str, set[str]] = {}
    for pkg, dists in get_packages_distributions().items():
        for dist in dists:
            normalized_dist = dist.lower().replace("-", "_")
            result.setdefault(normalized_dist, set()).add(pkg)
    return MappingProxyType({dist: frozenset(pkgs) for dist, pkgs in result.items()})


@lru_cache(maxsize=1024)
def _package_to_distributions_impl(package_name: str) -> Sequence[str] | None:
    return get_packages_distributions().get(package_name)


def package_to_distributions(package_name: str) -> list[str] | None:
    """Convert a package name to all its distribution names.

    Args:
        package_name: The name of the package

    Returns:
        List of distribution names if found, None otherwise.

    Example:
        >>> package_to_distributions('zope')  # namespace package
        ['zope.interface', 'zope.event']  # if both are installed
        >>> package_to_distributions('requests')
        ['requests']
        >>> package_to_distributions('nonexistent')
        None

    Notes:
        For namespace packages (like 'zope'), returns all related distributions.
        This is particularly useful for examining namespace package relationships.
    """
    dists = _package_to_distributions_impl(package_name)
    return list(dists) if dists is not None else None


@lru_cache(maxsize=1024)
def package_to_distribution(package_name: str) -> str | None:
    """Convert a package name to its distribution name.

    Args:
        package_name: The name of the package

    Returns:
        The distribution name if found, None otherwise

    Example:
        >>> package_to_distribution('PIL')
        'Pillow'
        >>> package_to_distribution('requests')
        'requests'
        >>> package_to_distribution('nonexistent')
        None
    """
    if not isinstance(package_name, str):
        msg = "Package name must be a string"
        raise TypeError(msg)

    # First try direct lookup
    pkg_dist_map = get_packages_distributions()
    if package_name in pkg_dist_map:
        return pkg_dist_map[package_name][0]

    # Try normalized lookup with and without underscore prefix
    try:
        normalized_package = package_name.lower().replace("-", "_")
    except (TypeError, AttributeError) as e:
        msg = "Package name must be a string"
        raise TypeError(msg) from e

    normalized_map = _get_normalized_pkg_dist_map()

    # Try exact match first
    if normalized_package in normalized_map:
        return normalized_map[normalized_package]

    # Try without underscore prefix
    clean_package = normalized_package.lstrip("_")
    if clean_package != normalized_package and clean_package in normalized_map:
        return normalized_map[clean_package]
    return None


# Create the implementation separately for type checking
@lru_cache(maxsize=1024)
def _distribution_to_package_impl(distribution_name: str, *, fallback: bool = False) -> str | None:
    result = _primary_package(distribution_name, distribution_to_packages(distribution_name))
    if result is None and fallback:
        return distribution_name.replace("-", "_").lower()
    return result


@overload
def distribution_to_package(distribution_name: str, *, fallback: Literal[True]) -> str: ...


@overload
def distribution_to_package(
    distribution_name: str, *, fallback: Literal[False] = False
) -> str | None: ...


def distribution_to_package(distribution_name: str, *, fallback: bool = False) -> str | None:
    """Convert a distribution name to its primary package name.

    If a distribution provides multiple packages, returns the primary one: the
    package named like the distribution, else the shortest name without a leading
    underscore (ties broken alphabetically). Use distribution_to_packages() to get
    all packages.

    Args:
        distribution_name: The name of the distribution
        fallback: Returns a normalized best guess even if no mapping found

    Returns:
        The primary package name if found, None otherwise

    Example:
        >>> distribution_to_package('Pillow')
        'PIL'
        >>> distribution_to_package('requests')
        'requests'
        >>> distribution_to_package('nonexistent')
        None
    """
    return _distribution_to_package_impl(distribution_name, fallback=fallback)


@lru_cache(maxsize=1024)
def distribution_to_packages(distribution_name: str) -> frozenset[str]:
    """Convert a distribution name to all its package names.

    Args:
        distribution_name: The name of the distribution

    Returns:
        A frozenset of the (importable) top-level package names of the distribution

    Example:
        >>> distribution_to_packages('Pillow')
        {'PIL'}
        >>> distribution_to_packages('python-dateutil')
        {'dateutil'}
        >>> distribution_to_packages('nonexistent')
        set()
    """
    normalized_dist = distribution_name.lower().replace("-", "_")
    normalized_map = _get_normalized_dist_pkg_map()
    return normalized_map.get(normalized_dist, frozenset())


def clear_caches() -> None:
    """Clear all function caches, the entry point cache included.

    This should be called when the underlying package distributions might have changed,
    for example after installing or removing packages.

    Example:
        >>> clear_caches()  # Clear all cached mappings
    """
    _get_normalized_pkg_dist_map.cache_clear()
    _get_normalized_dist_pkg_map.cache_clear()
    get_packages_distributions.cache_clear()
    _package_to_distributions_impl.cache_clear()
    package_to_distribution.cache_clear()
    _distribution_to_package_impl.cache_clear()
    distribution_to_packages.cache_clear()
    clear_entry_point_cache()


def get_cache_info() -> dict[str, str]:
    """Get information about the current state of all caches.

    Returns:
        A dictionary with cache statistics for each cached function

    Example:
        >>> info = get_cache_info()
        >>> print(info['package_to_distribution'])
        'CacheInfo(hits=42, misses=10, maxsize=1024, currsize=10)'
    """
    return {
        "normalized_pkg_dist_map": str(_get_normalized_pkg_dist_map.cache_info()),
        "normalized_dist_pkg_map": str(_get_normalized_dist_pkg_map.cache_info()),
        "get_packages_distributions": str(get_packages_distributions.cache_info()),
        "package_to_distribution": str(package_to_distribution.cache_info()),
        "package_to_distributions": str(_package_to_distributions_impl.cache_info()),
        "distribution_to_package": str(_distribution_to_package_impl.cache_info()),
        "distribution_to_packages": str(distribution_to_packages.cache_info()),
    }


if __name__ == "__main__":
    # Basic usage
    print(package_to_distribution("PIL"))  # 'Pillow'
    print(distribution_to_package("Pillow"))  # 'PIL'
    print(distribution_to_packages("python-dateutil"))  # {'dateutil'}

    # Case insensitive
    print(package_to_distribution("pil"))  # 'Pillow'
    print(distribution_to_packages("Python-DateUtil"))  # {'dateutil'}

    # Cache information
    print(get_cache_info())

    # Clear caches if needed
    clear_caches()
