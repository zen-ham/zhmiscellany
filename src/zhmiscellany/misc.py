import os, signal
from ._misc_supportfuncs import set_activity_timeout, activity
import zhmiscellany.math


def die():
    os.kill(os.getpid(), signal.SIGTERM)


def show_progress(things, total_things):
    print(f'\r{zhmiscellany.math.smart_percentage(things, total_things)}%', end='')
    if things == total_things:
        print('')
