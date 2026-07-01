"""Every ncp module must be non-empty and reachable from the entry points.

Guards against the package regressing into unused stub modules: importing
the demo entry point must pull in the entire ncp module tree.
"""
import importlib
import pkgutil
import sys

import ncp


def all_ncp_modules() -> list[str]:
    return [m.name for m in pkgutil.walk_packages(ncp.__path__, prefix="ncp.")]


def test_all_modules_import_and_are_non_empty():
    for name in all_ncp_modules():
        module = importlib.import_module(name)
        public = [n for n in vars(module) if not n.startswith("_")]
        assert public, f"{name} is an empty module"


def test_all_modules_reachable_from_entry_points():
    for mod in [m for m in list(sys.modules) if m.startswith(("ncp", "experiments"))]:
        del sys.modules[mod]
    importlib.import_module("experiments.demo")
    missing = [name for name in all_ncp_modules() if name not in sys.modules]
    assert not missing, f"modules not wired into the runtime import graph: {missing}"
