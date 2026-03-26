import os


def addon_root_dir():
    """Return the absolute path to the add-on's root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(filename):
    """Return the full path to an asset file in the add-on's assets/ folder.
    
    Args:
        filename: Name of the asset file (e.g., 'visualize_normals.blend')
    
    Returns:
        Absolute path to the asset file
    """
    return os.path.join(addon_root_dir(), "assets", filename)
