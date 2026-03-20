import importlib
import sys


_PACKAGE_NAME = __name__.split(".")[0]
_PACKAGE_ALIASES = {_PACKAGE_NAME, "artistant"}


# Blender's "Reload Scripts" re-executes this module; reload known addon submodules first.
if "artistant" in sys.modules or _PACKAGE_NAME in sys.modules:
	modules_to_reload = []

	for module_name, module in list(sys.modules.items()):
		if module is None:
			continue
		if module_name == __name__:
			continue
		if any(module_name.startswith(f"{pkg}.") for pkg in _PACKAGE_ALIASES):
			modules_to_reload.append(module)

	# Reload deeper modules first so parents can rebind updated symbols.
	modules_to_reload.sort(key=lambda m: m.__name__.count("."), reverse=True)
	for module in modules_to_reload:
		importlib.reload(module)


from .core.addon import register, unregister


__all__ = ("register", "unregister")
