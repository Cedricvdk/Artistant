import importlib
import sys

# Package identification for reload support
_PACKAGE_NAME = __name__.split(".")[0]
_PACKAGE_ALIASES = {_PACKAGE_NAME, "artistant"}


# Blender's "Reload Scripts" re-executes this module; reload known addon submodules first.
# This ensures changes to operators, properties, and UI are reflected without restarting Blender.
if "artistant" in sys.modules or _PACKAGE_NAME in sys.modules:
	# Collect all artistant submodules that are currently loaded
	modules_to_reload = []

	for module_name, module in list(sys.modules.items()):
		if module is None:
			continue
		if module_name == __name__:
			continue
		if any(module_name.startswith(f"{pkg}.") for pkg in _PACKAGE_ALIASES):
			modules_to_reload.append(module)

	# Reload deeper modules first (e.g., ops/export/unity_fbx.py before ops/export/, then before ops/)
	# This ensures parents can rebind updated child symbols after reload
	modules_to_reload.sort(key=lambda m: m.__name__.count("."), reverse=True)
	for module in modules_to_reload:
		importlib.reload(module)


# Import register/unregister functions from the central addon module
from .core.addon import register, unregister

__all__ = ("register", "unregister")
