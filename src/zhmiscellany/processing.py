import threading
import zhmiscellany.string
import concurrent.futures


def start_daemon(**kwargs):
    thread = threading.Thread(**kwargs)
    thread.daemon = True
    thread.start()
    return thread


def batch_threading(targets, max_threads):
    def execute_target(target):
        target[0](*target[1])

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(execute_target, target): target for target in targets}

        for future in concurrent.futures.as_completed(futures):
            del futures[future]