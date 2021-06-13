import os

def asset_path(absolute_path, base_path):
    path = os.path.relpath(absolute_path, base_path)
    return path.replace(os.path.sep, '/')


def absolute_asset_path(base_path, relative_path):
    return os.path.normpath(os.path.join(base_path, relative_path))
