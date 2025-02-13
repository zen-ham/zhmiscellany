import threading, os, signal, time, sys, shutil, ctypes
from ctypes import Structure, c_long, c_uint, c_int, POINTER, sizeof
import zhmiscellany.fileio
import zhmiscellany.misc


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


class POINT(Structure):
    _fields_ = [("x", c_long),
                ("y", c_long)]


class MOUSEINPUT(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_uint),
                ("dwFlags", c_uint),
                ("time", c_uint),
                ("dwExtraInfo", POINTER(c_uint))]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(Structure):
    _fields_ = [("type", c_int),
                ("union", INPUT_UNION)]


# Constants
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# Screen metrics
SCREEN_WIDTH, SCREEN_HEIGHT = zhmiscellany.misc.get_actual_screen_resolution()


def move_mouse(x: int, y: int):
    """Move mouse to specified coordinates."""
    # Convert coordinates to normalized coordinates (0-65535)
    normalized_x = int(x * (65535 / SCREEN_WIDTH))
    normalized_y = int(y * (65535 / SCREEN_HEIGHT))

    input_struct = INPUT(
        type=0,  # INPUT_MOUSE
        union=INPUT_UNION(
            mi=MOUSEINPUT(
                dx=normalized_x,
                dy=normalized_y,
                mouseData=0,
                dwFlags=MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE,
                time=0,
                dwExtraInfo=None
            )
        )
    )

    ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), sizeof(INPUT))


def mouse_down(button: int):
    """Press mouse button down. button: 1=left, 2=right, 3=middle"""
    if button not in [1, 2, 3]:
        raise ValueError("Button must be 1 (left), 2 (right), or 3 (middle)")

    flags = {
        1: MOUSEEVENTF_LEFTDOWN,
        2: MOUSEEVENTF_RIGHTDOWN,
        3: MOUSEEVENTF_MIDDLEDOWN
    }

    input_struct = INPUT(
        type=0,  # INPUT_MOUSE
        union=INPUT_UNION(
            mi=MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=0,
                dwFlags=flags[button],
                time=0,
                dwExtraInfo=None
            )
        )
    )

    ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), sizeof(INPUT))


def mouse_up(button: int):
    """Release mouse button. button: 1=left, 2=right, 3=middle"""
    if button not in [1, 2, 3]:
        raise ValueError("Button must be 1 (left), 2 (right), or 3 (middle)")

    flags = {
        1: MOUSEEVENTF_LEFTUP,
        2: MOUSEEVENTF_RIGHTUP,
        3: MOUSEEVENTF_MIDDLEUP
    }

    input_struct = INPUT(
        type=0,  # INPUT_MOUSE
        union=INPUT_UNION(
            mi=MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=0,
                dwFlags=flags[button],
                time=0,
                dwExtraInfo=None
            )
        )
    )

    ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), sizeof(INPUT))