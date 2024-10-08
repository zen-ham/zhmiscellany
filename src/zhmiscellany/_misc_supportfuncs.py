import threading, os, signal, time, sys, shutil
import zhmiscellany.fileio


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


def patch_rhg():  # patches random_header_generator library's missing files. this only matters if zhmiscellany has been compiled into a pyinstaller executable. zhmiscellany chooses to patch this broken package for the benefit of the user.
    if getattr(sys, 'frozen', False):
        # we are running in a PyInstaller bundle
        base_path = sys._MEIPASS
        cwd = os.getcwd()
        os.chdir(base_path)
        from ._py_resources import gen
        gen()
        rem_res = not os.path.exists('resources')
        os.makedirs(r'random_header_generator')
        shutil.move(r'resources\random_header_generator\data', r'random_header_generator')
        if rem_res:
            zhmiscellany.fileio.remove_folder('resources')
        os.chdir(cwd)
    else:
        # we are running in normal Python environment
        pass
