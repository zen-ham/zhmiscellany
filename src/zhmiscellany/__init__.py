from . import processing, misc, mousekb, discord, fileio, netio, string, math, image, list, dict, pipes, pastebin
import importlib
import inspect
import sys
from typing import TYPE_CHECKING

_MODULES = [
    'processing', 'misc', 'mousekb', 'discord', 'fileio',
    'netio', 'string', 'math', 'image', 'list', 'dict',
    'pipes', 'pastebin'
]

if TYPE_CHECKING:
    # This import provides type info from your generated stub.
    from .z import z as ZType
else:
    class _z:
        """Runtime implementation for the z shortcut container."""
        
        def __getattr__(self, name):
            return globals()[name]
        
        def __dir__(self):
            return [f for module in _MODULES
                    for f in dir(globals()[module])
                    if callable(globals()[module].__dict__.get(f))]
    
    
    # Create an instance that will hold all the functions.
    z = _z()


def _collect_functions():
    all_funcs = {}
    for mod_name in _MODULES:
        module = importlib.import_module(f'.{mod_name}', __package__)
        funcs = {
            name: func for name, func in inspect.getmembers(module)
            if inspect.isfunction(func) and func.__module__ == module.__name__
        }
        all_funcs.update(funcs)
        globals().update(funcs)
    
    # Populate the z instance with static references.
    for name, func in all_funcs.items():
        setattr(z, name, staticmethod(func))


_collect_functions()

# Export z for IDE autocompletion.
if TYPE_CHECKING:
    # This reassignment tells type checkers that z has type ZType.
    z: ZType

# Optionally add to __all__ so that z is explicitly exported.
__all__ = ['z']
