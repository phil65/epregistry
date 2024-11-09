# epregistry

[![PyPI License](https://img.shields.io/pypi/l/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Package status](https://img.shields.io/pypi/status/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Daily downloads](https://img.shields.io/pypi/dd/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Weekly downloads](https://img.shields.io/pypi/dw/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Monthly downloads](https://img.shields.io/pypi/dm/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Distribution format](https://img.shields.io/pypi/format/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Wheel availability](https://img.shields.io/pypi/wheel/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Python version](https://img.shields.io/pypi/pyversions/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Implementation](https://img.shields.io/pypi/implementation/epregistry.svg)](https://pypi.org/project/epregistry/)
[![Releases](https://img.shields.io/github/downloads/phil65/epregistry/total.svg)](https://github.com/phil65/epregistry/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/epregistry)](https://github.com/phil65/epregistry/graphs/contributors)
[![Github Discussions](https://img.shields.io/github/discussions/phil65/epregistry)](https://github.com/phil65/epregistry/discussions)
[![Github Forks](https://img.shields.io/github/forks/phil65/epregistry)](https://github.com/phil65/epregistry/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/epregistry)](https://github.com/phil65/epregistry/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/epregistry)](https://github.com/phil65/epregistry/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/epregistry)](https://github.com/phil65/epregistry/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/epregistry)](https://github.com/phil65/epregistry/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/epregistry)](https://github.com/phil65/epregistry/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/epregistry)](https://github.com/phil65/epregistry/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Github commits this week](https://img.shields.io/github/commit-activity/w/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Github commits this year](https://img.shields.io/github/commit-activity/y/phil65/epregistry)](https://github.com/phil65/epregistry)
[![Package status](https://codecov.io/gh/phil65/epregistry/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/epregistry/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyUp](https://pyup.io/repos/github/phil65/epregistry/shield.svg)](https://pyup.io/repos/github/phil65/epregistry/)

[Read the documentation!](https://phil65.github.io/epregistry/)

## Overview

The Entry Point Registry system provides a convenient way to manage and access Python entry points. It's particularly useful when you need to work with plugins, extensions, or any modular components in your Python applications.

## Basic Usage

### Creating a Registry

To start using the registry, create an instance for a specific entry point group:

```python
from epregistry import EntryPointRegistry

# Create a registry for console scripts
registry = EntryPointRegistry[Callable]("console_scripts")
```

> **💡 Tip: Type Hints**
> Use the generic type parameter to specify the expected type of your entry points. For example, `EntryPointRegistry[Callable]` indicates that the entry points are callable objects.

### Accessing Entry Points

#### Get a Single Entry Point

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
# -> dict[str, EntryPoint]
all_entry_points = registry.get_all()

# Load all entry points
# -> dict[str, Callable] (or whatever type you specified)
loaded_points = registry.load_all()
```

### Checking Entry Points

```python
# Check if an entry point exists
if "script_name" in registry:
    print("Entry point exists")

# Get the total number of entry points
count = len(registry)

# Iterate over all entry points
for entry_point in registry:
    print(entry_point.name)
```

## Advanced Features

### Metadata Access

Retrieve detailed information about an entry point:

```python
metadata = registry.get_metadata("script_name")
print(f"Module: {metadata['module']}")
print(f"Attribute: {metadata['attr']}")
print(f"Distribution: {metadata['dist']}")
print(f"Version: {metadata['version']}")
```

### Extension Point Directory

Find the installation directory of an extension point:

```python
directory = registry.get_extension_point_dir("script_name")
print(f"Extension is installed at: {directory}")
```

### Available Groups

Get a list of all available entry point groups in the system:

```python
from epregistry import available_groups

groups = available_groups()
print("Available entry point groups:", groups)
```

### Filtering and Searching

The Entry Point Registry provides powerful filtering and search capabilities to help you find specific entry points.

#### Filtering Entry Points

Filter entry points based on group, distribution, or name patterns:

```python
from epregistry import filter_entry_points

# Filter by group
flask_eps = filter_entry_points(group="flask.*")

# Filter by distribution
pytest_eps = filter_entry_points(distribution="pytest")

# Filter by name pattern (supports * and ? wildcards)
test_eps = filter_entry_points(name_pattern="test_*")

# Combine multiple filters
specific_eps = filter_entry_points(
    group="pytest11",
    distribution="pytest",
    name_pattern="*fixture*"
)
```

#### Searching Entry Points

Search across all entry points using a general query:

```python
from epregistry import search_entry_points

# Search everywhere
sql_related = search_entry_points("sql")

# Search with specific scope
results = search_entry_points(
    "test",
    include_groups=True,      # Search in group names
    include_names=True,       # Search in entry point names
    include_distributions=True # Search in distribution names
)
```

#### List Available Distributions

Get a list of all distributions that provide entry points:

```python
from epregistry import list_distributions

# Get all distributions with entry points
distributions = list_distributions()
print("Available distributions:", distributions)
```

> **💡 Tip: Filtering Patterns**
> The filtering system supports wildcards:
> - `*` matches any number of characters
> - `?` matches exactly one character
> - Patterns are case-insensitive

These search and filtering capabilities are particularly useful when:
- Exploring available plugins in a large system
- Debugging entry point configurations
- Building plugin management interfaces
- Finding specific extensions across multiple packages


## Integration with Package Management

The Entry Point Registry integrates with Python's [`importlib.metadata`](https://docs.python.org/3/library/importlib.metadata.html) system, making it compatible with:

- [📦 setuptools](https://setuptools.pypa.io/en/latest/)
- [📦 poetry](https://python-poetry.org/)
- Other packaging tools that follow the entry points specification

> **📝 Note: Automatic Caching**
> The registry implements automatic caching of entry points for better performance. The cache is initialized on first use and shared across all registry instances.
