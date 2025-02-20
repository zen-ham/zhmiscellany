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

def _inject_z():
    frame = inspect.currentframe()
    while frame:
        if frame.f_globals.get('__name__') != __name__:
            frame.f_globals['z'] = z
            break
        frame = frame.f_back

_inject_z()  # Get the module that imported this package