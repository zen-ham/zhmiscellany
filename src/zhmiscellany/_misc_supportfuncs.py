import threading, os, signal, time


_misc_action = 0
_misc_timeout_exists = 0


def do_timeout(timeout):
    global _misc_action, _misc_timeout_exists
    self_time = time.time()
    _misc_timeout_exists = self_time
    while True:
        time.sleep(0.1)
        if time.time() - _misc_action > timeout:
            os.kill(os.getpid(), signal.SIGTERM)
        if self_time != _misc_timeout_exists:
            return


def set_activity_timeout(timeout):
    global _misc_action
    _misc_action = time.time()
    threading.Thread(target=do_timeout, args=timeout).start()


def activity():
    global _misc_action
    _misc_action = time.time()