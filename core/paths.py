import os


def addon_root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(filename):
    return os.path.join(addon_root_dir(), "assets", filename)
