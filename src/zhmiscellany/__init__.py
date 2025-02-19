from . import processing, misc, mousekb, discord, fileio, netio, string, math, image, list, dict, pipes, pastebin

import importlib
import inspect

# Explicit module list (better than parsing the file)
_MODULES = [
    'processing', 'misc', 'mousekb', 'discord', 'fileio',
    'netio', 'string', 'math', 'image', 'list', 'dict',
    'pipes', 'pastebin'
]


# Collect functions from all modules
class Z:
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
        setattr(Z, func.__name__, func)


_collect_functions()

# Clean up internal machinery
del _MODULES, _collect_functions

# Package exports
__all__ = [*_MODULES, 'Z']