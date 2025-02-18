from ._processing_supportfuncs import batch_multiprocess, multiprocess
import threading, kthread
import traceback
import zhmiscellany.string
import concurrent.futures


def start_daemon(**kwargs):
    thread = threading.Thread(**kwargs)
    thread.daemon = True
    thread.start()
    return thread


def batch_threading(targets, max_threads, show_errors=True):
    def execute_target(target):
        try:
            target[0](*target[1])
        except Exception as e:
            if show_errors:
                print(traceback.format_exc())
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(execute_target, target): target for target in targets}

        for future in concurrent.futures.as_completed(futures):
            del futures[future]


def batch_multiprocess_threaded(targets_and_args, disable_warning=False, killable=False, daemon=False):
    if killable:
        thread_method = kthread.KThread
    else:
        thread_method = threading.Thread
    t = thread_method(target=batch_multiprocess, args=(targets_and_args, disable_warning))
    if daemon:
        t.daemon = True
    t.start()
    return t


def multiprocess_threaded(target, args=(), disable_warning=False, killable=False, daemon=False):
    return batch_multiprocess_threaded([(target, args)], disable_warning=False, killable=False, daemon=False)