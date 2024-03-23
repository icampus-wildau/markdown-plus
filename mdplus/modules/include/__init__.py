from os.path import dirname, basename, isfile, join
import glob

import mdplus.modules.include.md as md

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]


def main(*args, **kwargs):
    include_file = args[0]
    # if include_file.endswith(".md"):

    return md.main(*args, **kwargs)
