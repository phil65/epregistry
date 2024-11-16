from collections.abc import Mapping
from functools import cache, lru_cache
from importlib.metadata import packages_distributions
from typing import Literal, overload


@cache
def get_packages_distributions() -> Mapping[str, list[str]]:
    """Cached call for packages_distributions."""
    return packages_distributions()


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
def _get_normalized_dist_pkg_map() -> dict[str, set[str]]:
    """Cache the normalized distribution to package mapping.

    Returns:
        A dictionary mapping normalized distribution names to sets of package names.
    """
    result: dict[str, set[str]] = {}
    for pkg, dists in get_packages_distributions().items():
        for dist in dists:
            normalized_dist = dist.lower().replace("-", "_")
            if normalized_dist not in result:
                result[normalized_dist] = set()
            # For distribution_to_package, prefer unprefixed version if available
            clean_pkg = pkg.lstrip("_")
            result[normalized_dist].add(clean_pkg)
    return result


@lru_cache(maxsize=1024)
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
    pkg_dist_map = get_packages_distributions()
    return pkg_dist_map.get(package_name)


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
def _distribution_to_package_impl(
    distribution_name: str, *, fallback: bool = False
) -> str | None:
    packages = distribution_to_packages(distribution_name)
    result = next(iter(packages)) if packages else None

    if result is None and fallback:
        return distribution_name.replace("-", "_").lower()

    if fallback:
        assert result is not None
        return result
    return result


@overload
def distribution_to_package(
    distribution_name: str, *, fallback: Literal[True]
) -> str: ...


@overload
def distribution_to_package(
    distribution_name: str, *, fallback: Literal[False] = False
) -> str | None: ...


def distribution_to_package(
    distribution_name: str, *, fallback: bool = False
) -> str | None:
    """Convert a distribution name to its primary package name.

    If a distribution provides multiple packages, returns the primary one.
    Use distribution_to_packages() to get all packages.

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
def distribution_to_packages(distribution_name: str) -> set[str]:
    """Convert a distribution name to all its package names.

    Args:
        distribution_name: The name of the distribution

    Returns:
        A set of package names provided by the distribution

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
    return normalized_map.get(normalized_dist, set())


def clear_caches() -> None:
    """Clear all function caches.

    This should be called when the underlying package distributions might have changed,
    for example after installing or removing packages.

    Example:
        >>> clear_caches()  # Clear all cached mappings
    """
    _get_normalized_pkg_dist_map.cache_clear()
    _get_normalized_dist_pkg_map.cache_clear()
    get_packages_distributions.cache_clear()
    package_to_distributions.cache_clear()
    package_to_distribution.cache_clear()
    _distribution_to_package_impl.cache_clear()
    distribution_to_packages.cache_clear()


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
        "package_to_distributions": str(package_to_distributions.cache_info()),
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
