from zhmiscellanyrusteffect import *

globals().update({name: globals()[name] for name in dir() if not name.startswith("__")})