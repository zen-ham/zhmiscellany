from ._processing_supportfuncs import batch_threading
import threading


def start_daemon(**kwargs):
    thread = threading.Thread(**kwargs)
    thread.daemon = True
    thread.start()
    return thread
