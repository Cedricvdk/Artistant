import importlib
import sys

# Package identification for reload support
_PACKAGE_ROOT = __package__ or __name__
_PACKAGE_ALIASES = {_PACKAGE_ROOT}

# Keep a legacy alias for local-dev installs where the folder is named "artistant".
# This is intentionally narrow and never broadens to top-level namespaces like "bl_ext".
if _PACKAGE_ROOT != "artistant":
	_PACKAGE_ALIASES.add("artistant")


def _belongs_to_addon_module(module_name: str) -> bool:
	"""Return True if module_name is the addon package or one of its submodules."""
	return any(
		module_name == pkg or module_name.startswith(f"{pkg}.")
		for pkg in _PACKAGE_ALIASES
	)


def _is_reloadable_module(module) -> bool:
    # Return True only for modules that have a valid import spec/loader.
    spec = getattr(module, "__spec__", None)
    if spec is None:
        return False
    return getattr(spec, "loader", None) is not None


# Blender's "Reload Scripts" re-executes this module; reload known addon submodules first.
# This ensures changes to operators, properties, and UI are reflected without restarting Blender.
if any(_belongs_to_addon_module(name) for name in sys.modules):
    # Collect addon submodules that are currently loaded
    modules_to_reload = []

    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue
        if module_name == __name__:
            continue
        if _belongs_to_addon_module(module_name):
            modules_to_reload.append((module_name, module))

    # Reload deeper modules first (e.g., ops/export/unity_fbx.py before ops/export/, then before ops/)
    # This ensures parents can rebind updated child symbols after reload
    modules_to_reload.sort(key=lambda item: item[0].count("."), reverse=True)
    for module_name, module in modules_to_reload:
        if not _is_reloadable_module(module):
            # Clean stale leftovers from previous installs/renames that cannot be reloaded.
            sys.modules.pop(module_name, None)
            continue
        try:
            importlib.reload(module)
        except (ImportError, ModuleNotFoundError):
            # If a module disappeared or has no import spec, skip it and keep startup alive.
            sys.modules.pop(module_name, None)


# Import register/unregister functions from the central addon module
from .core.addon import register, unregister

__all__ = ("register", "unregister")
