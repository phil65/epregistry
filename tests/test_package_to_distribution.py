from __future__ import annotations

import pytest

from epregistry.package_to_distribution import (
    _get_normalized_dist_pkg_map,
    _get_normalized_pkg_dist_map,
    clear_caches,
    distribution_to_package,
    distribution_to_packages,
    get_cache_info,
    get_packages_distributions,
    package_to_distribution,
)


# Constants
KNOWN_PACKAGE = "yaml"
KNOWN_DISTRIBUTION = "PyYAML"
NONEXISTENT_PACKAGE = "this_package_does_not_exist_123456789"
NONEXISTENT_DISTRIBUTION = "this_distribution_does_not_exist_123456789"
MIXED_CASE_PACKAGE = "PyYAML"
HYPHENATED_NAME = "python-dateutil"
NORMALIZED_HYPHENATED_NAME = "python_dateutil"


@pytest.fixture(autouse=True)
def _clear_all_caches():
    """Clear all caches before each test."""
    clear_caches()


def test_package_to_distribution_known():
    """Test converting known package to distribution."""
    result = package_to_distribution(KNOWN_PACKAGE)
    assert isinstance(result, str)
    assert result == KNOWN_DISTRIBUTION


def test_package_to_distribution_nonexistent():
    """Test converting nonexistent package."""
    assert package_to_distribution(NONEXISTENT_PACKAGE) is None


def test_package_to_distribution_case_insensitive():
    """Test case insensitivity of package lookup."""
    original = package_to_distribution(KNOWN_PACKAGE)
    lower = package_to_distribution(KNOWN_PACKAGE.lower())
    upper = package_to_distribution(KNOWN_PACKAGE.upper())
    assert original == lower == upper


def test_distribution_to_package_known():
    """Test converting known distribution to package."""
    result = distribution_to_package(KNOWN_DISTRIBUTION)
    assert isinstance(result, str)
    assert result == KNOWN_PACKAGE


def test_distribution_to_package_nonexistent():
    """Test converting nonexistent distribution."""
    assert distribution_to_package(NONEXISTENT_DISTRIBUTION) is None


def test_distribution_to_package_case_insensitive():
    """Test case insensitivity of distribution lookup."""
    original = distribution_to_package(KNOWN_DISTRIBUTION)
    lower = distribution_to_package(KNOWN_DISTRIBUTION.lower())
    upper = distribution_to_package(KNOWN_DISTRIBUTION.upper())
    assert original == lower == upper


def test_distribution_to_packages_known():
    """Test converting known distribution to package set."""
    packages = distribution_to_packages(KNOWN_DISTRIBUTION)
    assert isinstance(packages, set)
    assert len(packages) > 0
    assert KNOWN_PACKAGE in packages


def test_distribution_to_packages_nonexistent():
    """Test converting nonexistent distribution to package set."""
    assert distribution_to_packages(NONEXISTENT_DISTRIBUTION) == set()


def test_distribution_to_packages_case_insensitive():
    """Test case insensitivity of distribution to packages lookup."""
    original = distribution_to_packages(KNOWN_DISTRIBUTION)
    lower = distribution_to_packages(KNOWN_DISTRIBUTION.lower())
    upper = distribution_to_packages(KNOWN_DISTRIBUTION.upper())
    assert original == lower == upper


def test_clear_caches():
    """Test cache clearing functionality."""
    # First access to populate caches
    package_to_distribution(KNOWN_PACKAGE)
    distribution_to_package(KNOWN_DISTRIBUTION)

    # Clear caches
    clear_caches()

    # Get cache info after clearing
    after_clear = get_cache_info()

    # Verify all caches are empty
    for cache_info in after_clear.values():
        assert "hits=" in cache_info
        assert "currsize=0" in cache_info


def test_get_cache_info():
    """Test cache info retrieval."""
    cache_info = get_cache_info()
    assert isinstance(cache_info, dict)
    expected_keys = {
        "get_packages_distributions",
        "normalized_pkg_dist_map",
        "normalized_dist_pkg_map",
        "package_to_distribution",
        "package_to_distributions",
        "distribution_to_package",
        "distribution_to_packages",
    }
    assert set(cache_info.keys()) == expected_keys


def test_cache_hits():
    """Test that caching is working properly."""
    # First call (miss)
    package_to_distribution(KNOWN_PACKAGE)

    # Second call (hit)
    package_to_distribution(KNOWN_PACKAGE)

    cache_info = get_cache_info()
    assert "hits=1" in cache_info["package_to_distribution"]


def test_mixed_case_handling():
    """Test handling of mixed case names."""
    result = package_to_distribution(MIXED_CASE_PACKAGE)
    lower_result = package_to_distribution(MIXED_CASE_PACKAGE.lower())
    assert result == lower_result


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        123,
        [],
        {},
        (),
    ],
)
def test_invalid_input_types(invalid_input):
    """Test handling of invalid input types."""
    with pytest.raises((AttributeError, TypeError)):
        package_to_distribution(invalid_input)

    with pytest.raises((AttributeError, TypeError)):
        distribution_to_package(invalid_input)

    with pytest.raises((AttributeError, TypeError)):
        distribution_to_packages(invalid_input)


def test_internal_mapping_types():
    """Test that internal mapping functions return correct types."""
    assert isinstance(get_packages_distributions(), dict)
    assert isinstance(_get_normalized_pkg_dist_map(), dict)
    assert isinstance(_get_normalized_dist_pkg_map(), dict)
