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
    assert isinstance(packages, frozenset)
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
    from collections.abc import Mapping

    assert isinstance(get_packages_distributions(), Mapping)
    assert isinstance(_get_normalized_pkg_dist_map(), dict)
    assert isinstance(_get_normalized_dist_pkg_map(), Mapping)


def _make_editable_dist(tmp_path, pth_content: str):
    """Create a fake .pth-based editable install of `foo-bar` in tmp_path."""
    from importlib.metadata import PathDistribution

    site = tmp_path / "site"
    dist_info = site / "foo_bar-1.0.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "METADATA").write_text("Metadata-Version: 2.4\nName: foo-bar\nVersion: 1.0\n")
    (dist_info / "RECORD").write_text("foo_bar-1.0.dist-info/METADATA,,\nfoo_bar.pth,,\n")
    (site / "foo_bar.pth").write_text(pth_content)
    return PathDistribution(dist_info)


def test_editable_packages_from_pth(tmp_path):
    """Packages of .pth-based editable installs are detected."""
    from epregistry.package_to_distribution import _editable_packages

    src = tmp_path / "src"
    (src / "foo_bar").mkdir(parents=True)
    (src / "foo_bar" / "__init__.py").write_text("")
    dist = _make_editable_dist(tmp_path, f"{src}\n")
    assert _editable_packages(dist) == {"foo_bar"}


def test_editable_packages_ignores_unrelated_pth(tmp_path):
    """Import lines and directories without a matching package are ignored."""
    from epregistry.package_to_distribution import _editable_packages

    other = tmp_path / "other"
    (other / "something_else").mkdir(parents=True)
    (other / "something_else" / "__init__.py").write_text("")
    dist = _make_editable_dist(tmp_path, f"import foo_bar\n# comment\n{other}\n")
    assert _editable_packages(dist) == set()


def test_own_distribution_resolves():
    """Epregistry resolves itself, also when installed in editable mode."""
    assert distribution_to_package("epregistry") == "epregistry"
    assert package_to_distribution("epregistry") == "epregistry"


def _run_with_hash_seed(seed: int, code: str) -> str:
    import os
    import subprocess
    import sys

    env = {**os.environ, "PYTHONHASHSEED": str(seed)}
    proc = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


def test_distribution_to_package_is_deterministic():
    """The primary package doesn't depend on the hash seed (pytest ships py and pytest)."""
    code = "from epregistry import distribution_to_package as d; print(d('pytest'))"
    results = {_run_with_hash_seed(seed, code) for seed in range(1, 7)}
    assert results == {"pytest"}


def test_primary_package_prefers_distribution_name():
    from epregistry.package_to_distribution import _primary_package

    assert _primary_package("pytest", {"py", "pytest", "_pytest"}) == "pytest"
    assert _primary_package("upathtools", {"upathtools_config", "upathtools"}) == "upathtools"
    assert _primary_package("logfire-sdk", {"logfire", "logfire_sdk"}) == "logfire_sdk"
    assert _primary_package("tomli", {"c787785866c7b801238d__mypyc", "tomli"}) == "tomli"
    assert _primary_package("Pillow", {"PIL"}) == "PIL"
    # no name match: names without a leading underscore first, shortest, then sorted
    assert _primary_package("foo", {"_hidden", "zz", "bb", "aaa"}) == "bb"


def test_distribution_to_package_keeps_leading_underscore():
    """A distribution whose only package starts with "_" gets its importable name."""
    from epregistry.package_to_distribution import _primary_package

    assert _primary_package("distutils-hack", {"_distutils_hack"}) == "_distutils_hack"


def test_distribution_to_packages_keeps_real_names(monkeypatch: pytest.MonkeyPatch):
    import sys

    mod = sys.modules["epregistry.package_to_distribution"]
    monkeypatch.setattr(mod, "packages_distributions", lambda: {"_private_pkg": ["private-pkg"]})
    monkeypatch.setattr(mod, "distributions", list)
    clear_caches()
    try:
        assert distribution_to_packages("private-pkg") == {"_private_pkg"}
        assert distribution_to_package("private-pkg") == "_private_pkg"
        # matching still ignores the underscore
        assert package_to_distribution("private_pkg") == "private-pkg"
    finally:
        monkeypatch.undo()
        clear_caches()


def test_cached_results_cannot_be_corrupted():
    """Results handed out don't share mutable state with the caches."""
    from epregistry import package_to_distributions

    packages = distribution_to_packages("pytest")
    with pytest.raises(AttributeError):
        packages.add("BOGUS")  # ty: ignore[unresolved-attribute]
    assert "BOGUS" not in distribution_to_packages("pytest")

    dists = package_to_distributions(KNOWN_PACKAGE)
    assert dists is not None
    dists.append("BOGUS")
    assert package_to_distributions(KNOWN_PACKAGE) == [KNOWN_DISTRIBUTION]

    mapping = get_packages_distributions()
    with pytest.raises(TypeError):
        mapping["bogus"] = ["x"]  # ty: ignore[invalid-assignment]
    assert "bogus" not in get_packages_distributions()


def test_clear_caches_also_clears_entry_points(monkeypatch: pytest.MonkeyPatch):
    from importlib.metadata import EntryPoint

    from epregistry import epregistry as mod
    from epregistry.epregistry import EntryPointRegistry

    ep = EntryPoint(name="x", value="os:getcwd", group="epregistry.test.clear")
    EntryPointRegistry("console_scripts").names()  # build the cache
    monkeypatch.setattr(mod, "entry_points", lambda: [ep])
    clear_caches()
    try:
        assert EntryPointRegistry("epregistry.test.clear").names() == ["x"]
    finally:
        monkeypatch.undo()
        clear_caches()
