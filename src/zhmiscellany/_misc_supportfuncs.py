import threading, os, signal, time, sys, shutil, ctypes, math
from ctypes import Structure, c_long, c_uint, c_int, POINTER, sizeof
import zhmiscellany.fileio
import sys

# Windows-specific imports
if sys.platform == "win32":
    try:
        import win32api
        from ctypes import windll
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
        print("Warning: Windows modules not available - Windows functionality disabled")
else:
    WIN32_AVAILABLE = False


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
if WIN32_AVAILABLE:
    patch_rhg()


def patch_cpp():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    
    anyway = False
    from ._resource_files_lookup import resource_files_lookup
    for file in resource_files_lookup:
        if not os.path.exists(os.path.join(base_path, file)):
            anyway = True  # missing file detected
            break
    
    fn = 'fast_array_diff.cp310-win_amd64.pyd'
    
    tp = os.path.join(base_path, fn)
    
    cwd = os.getcwd()
    if (not os.path.exists(tp)) or anyway:
        os.chdir(base_path)
        from ._py_resources import gen
        gen()
        shutil.copy2(os.path.join(base_path, 'resources', fn), tp)
        os.chdir(cwd)

if WIN32_AVAILABLE:
    patch_cpp()

import ctypes
import os
import math
import sys
from ctypes import c_int, c_uint, c_long, POINTER, Structure, sizeof, byref, c_ulong, c_void_p

# --- OS Detection ---
IS_LINUX = not WIN32_AVAILABLE

# --- Windows Imports & Structures ---
if WIN32_AVAILABLE:
    windll = ctypes.windll

if WIN32_AVAILABLE:
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


    # Windows Constants
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040

# --- Linux / X11 Setup ---
if IS_LINUX:
    try:
        # Load X11 and XTest (required for fake inputs)
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
        xtst = ctypes.cdll.LoadLibrary("libXtst.so.6")

        # Setup Display
        display = x11.XOpenDisplay(None)
        root_window = x11.XDefaultRootWindow(display)

    except OSError:
        print("Error: Could not load X11 or Xtst libraries. Ensure libx11-6 and libxtst6 are installed.")
        x11 = None
        xtst = None


# --- Screen Metrics ---
def get_actual_screen_resolution():
    if WIN32_AVAILABLE:
        if WIN32_AVAILABLE:
            hdc = windll.user32.GetDC(0)
            width = windll.gdi32.GetDeviceCaps(hdc, 118)  # HORZRES
            height = windll.gdi32.GetDeviceCaps(hdc, 117)  # VERTRES
            windll.user32.ReleaseDC(0, hdc)
            return width, height
        return 1920, 1080
    elif IS_LINUX and x11:
        screen_num = 0
        width = x11.XDisplayWidth(display, screen_num)
        height = x11.XDisplayHeight(display, screen_num)
        return width, height
    else:
        return 1920, 1080


SCREEN_WIDTH, SCREEN_HEIGHT = get_actual_screen_resolution()

# --- Globals ---
calibrated = False
calipass = False
calibration_multiplier_x = 1.0
calibration_multiplier_y = 1.0


# --- Functions ---

def move_mouse(x: int, y: int, relative=False):
    if WIN32_AVAILABLE:
        if not relative:
            # Convert coordinates to normalized coordinates (0-65535)
            normalized_x = int(x * (65535 / SCREEN_WIDTH))
            normalized_y = int(y * (65535 / SCREEN_HEIGHT))
            dwflags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE
        else:
            calibrate()
            if calibrated:
                normalized_x = math.ceil(x * calibration_multiplier_x)
                normalized_y = math.ceil(y * calibration_multiplier_y)
            else:
                normalized_x = x
                normalized_y = y
            dwflags = MOUSEEVENTF_MOVE

        input_struct = INPUT(
            type=0,
            union=INPUT_UNION(
                mi=MOUSEINPUT(
                    dx=normalized_x,
                    dy=normalized_y,
                    mouseData=0,
                    dwFlags=dwflags,
                    time=0,
                    dwExtraInfo=None
                )
            )
        )
        windll.user32.SendInput(1, ctypes.byref(input_struct), sizeof(INPUT))

    elif IS_LINUX and x11:
        # XWarpPointer(display, src_w, dest_w, src_x, src_y, src_width, src_height, dest_x, dest_y)
        if relative:
            # Move relative to current position (None as dest_window usually means relative move,
            # but standard practice is None src, None dest = move relative to current position)
            x11.XWarpPointer(display, None, None, 0, 0, 0, 0, int(x), int(y))
        else:
            # Absolute move relative to Root Window
            x11.XWarpPointer(display, None, root_window, 0, 0, 0, 0, int(x), int(y))

        x11.XFlush(display)


def get_mouse_xy():
    if WIN32_AVAILABLE:
        if WIN32_AVAILABLE:
            return win32api.GetCursorPos()
        return 0, 0
    elif IS_LINUX and x11:
        root_id = c_ulong()
        child_id = c_ulong()
        root_x = c_int()
        root_y = c_int()
        win_x = c_int()
        win_y = c_int()
        mask = c_uint()

        # XQueryPointer returns True if pointer is on the same screen
        result = x11.XQueryPointer(display, root_window,
                                   byref(root_id), byref(child_id),
                                   byref(root_x), byref(root_y),
                                   byref(win_x), byref(win_y),
                                   byref(mask))
        if result:
            return root_x.value, root_y.value
        return 0, 0
    else:
        return 0, 0


def calibrate():
    global calibration_multiplier_x, calibration_multiplier_y, calibrated, calipass

    # Linux (X11) relative movement is usually 1:1 pixel accurate via XWarpPointer
    # so we skip the calibration routine.
    if IS_LINUX:
        calibrated = True
        calipass = True
        calibration_multiplier_x = 1.0
        calibration_multiplier_y = 1.0
        return

    if not WIN32_AVAILABLE:
        return

    if calibrated:
        return
    if calipass:
        return

    calipass = True
    # calibrate relative movement, required because windows is weird
    original_mouse_point = get_mouse_xy()
    calibration_distance = 128
    moved_pos = (0, 0)
    lim = 64
    i = 0
    while ((not moved_pos[0]) or (not moved_pos[1])) and i < lim:
        i += 1
        move_mouse(0, 0)
        move_mouse(calibration_distance, calibration_distance, relative=True)
        moved_pos = get_mouse_xy()
    if not i < lim:
        raise Exception('Relative mouse movement could not be calibrated.')

    # Avoid division by zero
    if moved_pos[0] != 0:
        calibration_multiplier_x = calibration_distance / moved_pos[0]
    if moved_pos[1] != 0:
        calibration_multiplier_y = calibration_distance / moved_pos[1]

    calibrated = True
    move_mouse(original_mouse_point[0], original_mouse_point[1])


def mouse_down(button: int):
    """Press mouse button down. button: 1=left, 2=right, 3=middle"""
    if button not in [1, 2, 3]:
        raise ValueError("Button must be 1 (left), 2 (right), or 3 (middle)")

    if WIN32_AVAILABLE:
        flags = {
            1: MOUSEEVENTF_LEFTDOWN,
            2: MOUSEEVENTF_RIGHTDOWN,
            3: MOUSEEVENTF_MIDDLEDOWN
        }
        input_struct = INPUT(
            type=0,
            union=INPUT_UNION(
                mi=MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flags[button], time=0, dwExtraInfo=None)
            )
        )
        windll.user32.SendInput(1, ctypes.byref(input_struct), sizeof(INPUT))

    elif IS_LINUX and xtst:
        # Linux X11 Button Mapping: 1=Left, 2=Middle, 3=Right
        # Input Mapping: 1=Left, 2=Right, 3=Middle
        linux_button_map = {1: 1, 2: 3, 3: 2}

        # XTestFakeButtonEvent(display, button, is_press, delay)
        xtst.XTestFakeButtonEvent(display, linux_button_map[button], True, 0)
        x11.XFlush(display)


def mouse_up(button: int):
    """Release mouse button. button: 1=left, 2=right, 3=middle"""
    if button not in [1, 2, 3]:
        raise ValueError("Button must be 1 (left), 2 (right), or 3 (middle)")

    if WIN32_AVAILABLE:
        flags = {
            1: MOUSEEVENTF_LEFTUP,
            2: MOUSEEVENTF_RIGHTUP,
            3: MOUSEEVENTF_MIDDLEUP
        }
        input_struct = INPUT(
            type=0,
            union=INPUT_UNION(
                mi=MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flags[button], time=0, dwExtraInfo=None)
            )
        )
        windll.user32.SendInput(1, ctypes.byref(input_struct), sizeof(INPUT))

    elif IS_LINUX and xtst:
        # Linux X11 Button Mapping: 1=Left, 2=Middle, 3=Right
        linux_button_map = {1: 1, 2: 3, 3: 2}

        # XTestFakeButtonEvent(display, button, is_press, delay)
        xtst.XTestFakeButtonEvent(display, linux_button_map[button], False, 0)
        x11.XFlush(display)