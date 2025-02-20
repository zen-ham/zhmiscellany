from . import processing, misc, mousekb, discord, fileio, netio, string, math, image, list, dict, pipes, pastebin

import importlib
import inspect
import sys

_MODULES = [
    'processing', 'misc', 'mousekb', 'discord', 'fileio',
    'netio', 'string', 'math', 'image', 'list', 'dict',
    'pipes', 'pastebin'
]


# Collect functions from all modules
class z:
    """Aggregate of all package functions"""
    pass


def _collect_functions():
    all_funcs = []
    for mod_name in _MODULES:
        module = importlib.import_module(f'.{mod_name}', __package__)
        
        # Get functions defined IN the module (not imported ones)
        funcs = [
            func for _, func in inspect.getmembers(module)
            if inspect.isfunction(func) and func.__module__ == module.__name__
        ]
        
        all_funcs.extend(funcs)
    
    # Add to class namespace
    for func in all_funcs:
        setattr(z, func.__name__, func)


_collect_functions()

del _MODULES, _collect_functions

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['z'] = z