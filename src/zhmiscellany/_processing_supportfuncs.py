import threading, time
import zhmiscellany.string


def count_threads_by_string(string):
    count = 0
    for thread in threading.enumerate():
        if isinstance(thread, threading.Thread) and string in thread.name:
            count += 1
    return count


def batch_threading(targets, threads):
    batch_string = zhmiscellany.string.get_universally_unique_string()
    for target in targets:
        while count_threads_by_string(batch_string) >= threads:
            time.sleep(0.01)
        threading.Thread(target=target[0], args=target[1], name=f'{batch_string}_{zhmiscellany.string.get_universally_unique_string()}').start()