# AGENTS.md

## Overview

`epregistry` is a small, dependency-free library around `importlib.metadata`: cached,
generically typed registries for entry points (by group or by module), discovery/search
helpers, and package-name <-> distribution-name conversion. It is used by other projects
(e.g. mknodes), so treat the public API in `src/epregistry/__init__.py` as stable.

## Architecture

- `src/epregistry/epregistry.py`: entry point registries.
  - `_get_entry_point_cache()` builds the module-global `_entry_point_cache`
    (`{group: {name: EntryPoint}}`, first of same-named entry points wins) once, under a lock
    (double-checked); every registry and helper shares it and treats it as read-only.
    `clear_entry_point_cache()` drops it (and the per-Distribution name cache `_dist_names`
    used by the search/filter helpers).
  - `EntryPointRegistry[T]`: view on one group (`get`, `load`, `__getitem__`, `names`,
    `get_all`, `load_all`, `get_metadata`, `get_extension_point_dir`). Looks the group up
    on each access (an unknown group is empty and never added); `get_all()` returns a copy.
  - `ModuleEntryPointRegistry[T]`: view on all entry points whose `ep.module` equals the
    given module or starts with `"<module>."`, grouped by group (per-instance cache, rebuilt
    when the global cache was refreshed; `get_all`/`get_group` return copies).
  - Free functions: `available_groups`, `filter_entry_points` (fnmatch wildcards,
    case-insensitive), `search_entry_points` (substring), `list_distributions`,
    `get_all_entry_points`.
- `src/epregistry/package_to_distribution.py`: name conversion on top of
  `importlib.metadata.packages_distributions()`.
  - `get_packages_distributions()` (cached) also adds packages of `.pth`-based editable
    installs (uv_build editables only ship a `.pth` file) via `_editable_packages()`.
  - Normalized lookup maps (`_get_normalized_pkg_dist_map`, `_get_normalized_dist_pkg_map`)
    lowercase and map `-` to `_`; leading underscores are stripped only for matching, the
    returned package names are the real (importable) ones.
  - Cached results are read-only (`MappingProxyType`, tuples, `frozenset`) or copies, so
    callers can't corrupt the caches.
  - `package_to_distribution(s)`, `distribution_to_package(s)` (`fallback=True` returns a
    normalized guess instead of `None`), `clear_caches()` (also clears the entry point
    cache), `get_cache_info()`. `distribution_to_package` picks deterministically
    (`_primary_package`: the package named like the distribution, else no leading
    underscore, shortest, alphabetical).
- `src/epregistry/log.py`: `get_logger()` helper (currently not used internally).
- `src/epregistry/__init__.py`: public re-exports and `__all__`; `__version__` comes from
  installed metadata.

## Where to look

| Task | File |
| --- | --- |
| Group/module registry behavior, caching | `src/epregistry/epregistry.py` |
| Search / filter / discovery helpers | `src/epregistry/epregistry.py` (bottom) |
| Package <-> distribution mapping, editable installs | `src/epregistry/package_to_distribution.py` |
| Public API surface | `src/epregistry/__init__.py` |
| Tests | `tests/test_epregistry.py`, `tests/test_module_epregistry.py`, `tests/test_package_to_distribution.py`, fixtures in `tests/conftest.py` |
| CI | `.github/workflows/build.yml`, `.github/workflows/documentation.yml` |
| Dev tasks | `duties.py` |

## Commands

```bash
uv sync --all-extras                 # setup (default groups: dev, lint, docs)
uv run pytest                        # tests (duty: `uv run duty test`)
uvx ruff check . && uvx ruff format --check .   # lint (CI uses the latest ruff)
uv run ty check                      # type check, src/ only; warnings fail CI
uv run deptry src                    # dependency hygiene
uv run mknodes build          # docs (duty: `uv run duty build`; `serve` to preview)
uv build                             # build sdist/wheel (uv_build backend)
uv run duty lint                     # ruff fix + format + ty (duty comes in via the docs group)
uv run duty version patch            # bump version, commit and tag (owner only)
```

## Conventions

- Python >= 3.13; PEP 695 generics with defaults (`class EntryPointRegistry[T = Any]`).
- `from __future__ import annotations` everywhere; type-only imports under `TYPE_CHECKING`.
- Google-style docstrings without types in `Args`; ruff config (line length 100, preview
  formatting, wide rule set) is in `pyproject.toml`. Markdown code blocks (README) are
  ruff-formatted too.
- Tests are plain pytest functions (no classes). They run against the real installed
  environment (`console_scripts`, `pytest11`, `_pytest` module, `PyYAML`,
  `python-dateutil`), so dev dependencies matter.
- No runtime dependencies; keep it that way.

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `copier-phil65`). Workflows,
  `duties.py`, `.pre-commit-config.yaml` and most of `pyproject.toml` come from the template;
  avoid hand-editing them. Add dependencies only below the `# Only add below (Copier)` markers.
- The global entry point cache is filled once per process and never invalidated: entry points
  of packages installed later are not seen. `package_to_distribution.clear_caches()` only
  clears the name-conversion caches, not the entry point cache.
- `EntryPointRegistry("x")` inserts an empty group `"x"` into the shared cache, so
  `available_groups()` also lists groups that were only queried.
- `get_extension_point_dir()` only works for loaded objects with a `__file__` (modules);
  it asserts otherwise.
- Editable-install detection only covers the case where the normalized distribution name is
  a package/module in a directory listed in the distribution's `.pth` file. Editables whose
  import name differs from the distribution name still return `None` (use `fallback=True`).
- pytest >= 9: pytest's console scripts point to `_pytest.config`, not `pytest`.
- `uv.lock` is gitignored. The docs group pulls in a large dependency tree (mkdocs-mknodes).
