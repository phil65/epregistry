"""epregistry: main package.

A registry for entry points (cached and generically typed).
"""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("epregistry")
__title__ = "epregistry"

__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2024 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/epregistry"

from importlib.metadata import EntryPoint
from epregistry.epregistry import (
    EntryPointRegistry,
    ModuleEntryPointRegistry,
    available_groups,
    filter_entry_points,
    search_entry_points,
    list_distributions,
    get_all_entry_points,
)
from epregistry.package_to_distribution import (
    package_to_distributions,
    package_to_distribution,
    distribution_to_packages,
    distribution_to_package,
    get_packages_distributions,
)


__all__ = [
    "EntryPoint",
    "EntryPointRegistry",
    "ModuleEntryPointRegistry",
    "__version__",
    "available_groups",
    "distribution_to_package",
    "distribution_to_packages",
    "filter_entry_points",
    "get_all_entry_points",
    "get_packages_distributions",
    "list_distributions",
    "package_to_distribution",
    "package_to_distributions",
    "search_entry_points",
]
