from . import processing, misc, mousekb, discord, fileio, netio, string, math, image, list, dict, pipes, pastebin
import importlib
import inspect
from typing import TYPE_CHECKING

_MODULES = [
    'processing', 'misc', 'mousekb', 'discord', 'fileio',
    'netio', 'string', 'math', 'image', 'list', 'dict',
    'pipes', 'pastebin'
]

if TYPE_CHECKING:
    # For IDE autocompletion during development
    from .z_stub import z  # Reference to stub file
else:
    # Runtime implementation
    class z:
        """Aggregate of all package functions (runtime version)"""
        
        def __getattr__(self, name):
            return globals()[name]  # Direct access to module-level functions
        
        def __dir__(self):
            return [f for module in _MODULES for f in dir(globals()[module]) if
                    callable(globals()[module].__dict__.get(f))]


# Runtime population (for actual execution)
def _collect_functions():
    all_funcs = {}
    for mod_name in _MODULES:
        module = importlib.import_module(f'.{mod_name}', __package__)
        funcs = {
            name: func for name, func in inspect.getmembers(module)
            if inspect.isfunction(func) and func.__module__ == module.__name__
        }
        all_funcs.update(funcs)
        globals().update(funcs)  # Also expose functions at package level
    
    # Create alias references in z class
    for name, func in all_funcs.items():
        setattr(z, name, staticmethod(func))


_collect_functions()

# Cleanup
del _MODULES, _collect_functions

if '__main__' in sys.modules:
    sys.modules['__main__'].__dict__['z'] = z