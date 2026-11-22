# epregistry

[![PyPI License](https://img.shields.io/pypi/l/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Package status](https://img.shields.io/pypi/status/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Monthly downloads](https://img.shields.io/pypi/dm/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Distribution format](https://img.shields.io/pypi/format/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Wheel availability](https://img.shields.io/pypi/wheel/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Python version](https://img.shields.io/pypi/pyversions/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Implementation](https://img.shields.io/pypi/implementation/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Releases](https://img.shields.io/github/downloads/phil65/epregistry/total.svg)](https://github.com/phil65/epregistry/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/epregistry)](https://github.com/phil65/epregistry/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/epregistry)](https://github.com/phil65/epregistry/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/epregistry)](https://github.com/phil65/epregistry/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/epregistry)](https://github.com/phil65/epregistry/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/epregistry)](https://github.com/phil65/epregistry/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/epregistry)](https://github.com/phil65/epregistry/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/epregistry)](https://github.com/phil65/epregistry/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/epregistry)](https://github.com/phil65/epregistry/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Package status](https://codecov.io/gh/phil65/epregistry/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/epregistry/)

[Read the documentation!](https://phil65.github.io/epregistry/)

## Overview

`epregistry` is a small, dependency-free layer over `importlib.metadata` for working with
Python entry points. All entry points are read once and cached, and registries are generically
typed so that loaded plugins get the type you expect. It offers two ways to access entry points:

- Group-based access: Work with all entry points in a specific group
- Module-based access: Work with all entry points provided by a specific module

On top of that it provides discovery/search helpers and cached conversion between package
(import) names and distribution names. This makes it useful for plugin systems, extensions,
or any modular components in Python applications.

## Installation

```bash
pip install epregistry
# or
uv add epregistry
```

Requires Python 3.13 or newer.

## Basic Usage

### Group-based Registry

When you want to work with entry points organized by their group:

```python
from collections.abc import Callable

from epregistry import EntryPointRegistry

# Create a registry for console scripts
registry = EntryPointRegistry[Callable]("console_scripts")

# Get and load an entry point
script = registry.load("my-script")

# Get all entry points in the group
all_scripts = registry.get_all()
```

### Module-based Registry

When you want to work with all entry points provided by a specific module:

```python
from typing import Any

from epregistry import ModuleEntryPointRegistry

# Create a registry for a specific module
registry = ModuleEntryPointRegistry[Any]("your_module_name")

# Get all groups that have entry points from this module
groups = registry.groups()

# Get entry points for a specific group
group_eps = registry.get_group("console_scripts")

# Load all entry points for a group
loaded_eps = registry.load_group("console_scripts")
```

> **💡 Tip: Type Hints**
> Use the generic type parameter to specify the expected type of your entry points.
> For example, `EntryPointRegistry[Callable]` indicates that the entry points are callable objects.

### Working with Group-based Registry

#### Get Entry Points

```python
# Get an entry point (returns None if not found)
entry_point = registry.get("script_name")

# Get and load an entry point (returns None if not found)
loaded_entry_point = registry.load("script_name")

# Get an entry point with exception handling
try:
    entry_point = registry["script_name"]
except KeyError:
    print("Entry point not found")
```

#### Working with Multiple Entry Points

```python
# Get all entry point names
names = registry.names()

# Get all entry points as a dictionary
all_entry_points = registry.get_all()  # dict[str, EntryPoint]

# Load all entry points
loaded_points = registry.load_all()  # dict[str, T]
```

### Working with Module-based Registry

#### Get Entry Points by Group

```python
# Get all entry points for a specific group
eps = registry.get_group("console_scripts")

# Load all entry points for a group
loaded_eps = registry.load_group("console_scripts")
```

#### Access All Entry Points

```python
# Get all groups that contain entry points from this module
groups = registry.groups()

# Get all entry points organized by group
all_eps = registry.get_all()  # dict[str, list[EntryPoint]]

# Load all entry points from all groups
loaded_eps = registry.load_all()  # dict[str, list[T]]
```

### Common Operations

```python
# Check if an entry point exists
if "script_name" in registry:
    print("Entry point exists")

# Get the total number of entry points
count = len(registry)

# Iterate over entry points
for entry_point in registry:
    print(entry_point.name)
```

## Advanced Features

### Metadata Access

```python
# For group-based registry
metadata = registry.get_metadata("script_name")
print(f"Module: {metadata['module']}")
print(f"Attribute: {metadata['attr']}")
print(f"Distribution: {metadata['dist']}")
print(f"Version: {metadata['version']}")
```

### Extension Point Directory

For entry points that point to a module (i.e. the loaded object has a `__file__`),
get the directory the module is installed in:

```python
# For group-based registry
directory = registry.get_extension_point_dir("plugin_name")
print(f"Extension is installed at: {directory}")
```

### Discovery and Search

```python
from epregistry import (
    available_groups,
    filter_entry_points,
    search_entry_points,
    list_distributions,
)

# Get all available groups
groups = available_groups()

# Filter entry points
flask_eps = filter_entry_points(group="flask.*")
pytest_eps = filter_entry_points(distribution="pytest")
test_eps = filter_entry_points(name_pattern="test_*")

# Search across all entry points
results = search_entry_points(
    "test", include_groups=True, include_names=True, include_distributions=True
)

# List all distributions with entry points
distributions = list_distributions()
```

> **💡 Tip: Filtering Patterns**
> The filtering system supports wildcards:
> - `*` matches any number of characters
> - `?` matches exactly one character
> - Patterns are case-insensitive

## Package and Distribution Name Conversion

The package also contains helpers to convert between package (import) names and distribution names.
The mapping is cached as well; only the first conversion takes time to build the index.

```python
from epregistry import (
    distribution_to_package,
    distribution_to_packages,
    package_to_distribution,
    package_to_distributions,
)

# Convert package name to distribution
dist_name = package_to_distribution("PIL")  # Returns 'Pillow'
dist_name = package_to_distribution("requests")  # Returns 'requests'

# Convert distribution to primary package
pkg_name = distribution_to_package("Pillow")  # Returns 'PIL'
pkg_name = distribution_to_package("requests")  # Returns 'requests'

# All packages of a distribution / all distributions of a (namespace) package
pkgs = distribution_to_packages("python-dateutil")  # Returns {'dateutil'}
dists = package_to_distributions("zope")  # e.g. ['zope.interface', 'zope.event']

# Return a normalized best guess instead of None if no mapping is found
pkg_name = distribution_to_package("some-dist", fallback=True)  # 'some_dist'
```

Editable installs that only ship a `.pth` file (e.g. built with `uv_build`) are resolved
when the normalized distribution name is importable from the path in that `.pth` file.

## Integration with Package Management

The Entry Point Registry integrates with Python's [`importlib.metadata`](https://docs.python.org/3/library/importlib.metadata.html) system, making it compatible with:

- [📦 setuptools](https://setuptools.pypa.io/en/latest/)
- [📦 uv](https://docs.astral.sh/uv/)
- [📦 poetry](https://python-poetry.org/)
- Other packaging tools that follow the entry points specification

> **📝 Note: Automatic Caching**
> Both registry types implement automatic caching of entry points for better performance.
> The cache is initialized on first use and shared across all registry instances.
> Entry points of packages installed after the cache was built are not picked up.
