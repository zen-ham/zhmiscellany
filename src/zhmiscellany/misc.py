import os, signal
from ._misc_supportfuncs import set_activity_timeout, activity


def die():
    os.kill(os.getpid(), signal.SIGTERM)
