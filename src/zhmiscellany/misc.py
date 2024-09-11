import os, signal, time, importlib
from ._misc_supportfuncs import set_activity_timeout, activity
import zhmiscellany.math
import zhmiscellany.string
import win32api, win32con, time, hashlib, ctypes, sys


def die():
    os.kill(os.getpid(), signal.SIGTERM)


def show_progress(things, total_things, extra_data='', smart_ratelimit=False, max_prints=1000):
    do_print = True

    if smart_ratelimit:
        if total_things > max_prints:
            if not smart_every_nth(things, round(total_things/max_prints), total_things):
                do_print = False

    if do_print:
        print(f'\r{zhmiscellany.math.smart_percentage(things, total_things)}% {extra_data}', end='')
    if things == total_things:
        print('')


def every_nth(number, n):
    if number % n == 0:
        return True
    return False


def smart_every_nth(number, n, total):
    if number % n == 0:
        return True
    if number == total:
        return True
    return False


def calculate_eta(timestamps, total_timestamps):
    if not timestamps:
        return "Not enough data to calculate ETA."

    if total_timestamps <= len(timestamps):
        return "All timestamps recorded."

    # Calculate average time per timestamp
    total_time = timestamps[-1] - timestamps[0]
    average_time_per_timestamp = total_time / len(timestamps)

    # Calculate remaining time based on the average time per timestamp
    remaining_timestamps = total_timestamps - len(timestamps)
    estimated_remaining_time = remaining_timestamps * average_time_per_timestamp

    # Calculate the estimated arrival time
    current_time = time.time()
    estimated_arrival_time = current_time + estimated_remaining_time

    return zhmiscellany.string.timestamp_to_time(estimated_arrival_time)


def decide(options, text):
    output = input(f'{text} ({"/".join(options)})')
    while not output in options:
        output = input(f'{text} ({"/".join(options)})')
    return output


def import_module_from_path(path, module_name=None):
    if not module_name:
        module_name = zhmiscellany.string.get_universally_unique_string()
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def click_pixel(x=None, y=None, click_duration=None, right_click=False, shift=False, ctrl=False, act_start=True, act_end=True, middle_click=False, click_end_duration=None, double_click=False):
    if (x is None and y is not None) or (x is not None and y is None):
        raise Exception('x and y need to be either both defined or neither defined, you passed one and not the other.')

    keys_down = []

    if ctrl:
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        keys_down.append(win32con.VK_CONTROL)

    if shift:
        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        keys_down.append(win32con.VK_SHIFT)

    if x is not None and y is not None:
        win32api.SetCursorPos((x, y))

    if middle_click:
        if act_start:
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        if click_duration:
            high_precision_sleep(click_duration)
        if act_end:
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
    elif right_click:
        if act_start:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        if click_duration:
            high_precision_sleep(click_duration)
        if act_end:
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    else:
        if act_start:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        if click_duration:
            high_precision_sleep(click_duration)
        if act_end:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    for key in keys_down:
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

    if click_end_duration:
        high_precision_sleep(click_end_duration)

    if double_click:
        click_pixel(x, y, click_duration, right_click, shift, ctrl, act_start, act_end, middle_click, click_end_duration)


def type_string(text, delay=None, key_hold_time=None):
    # Dictionary mapping characters to their virtual key codes and shift state
    char_to_vk = {
        'a': (0x41, False), 'b': (0x42, False), 'c': (0x43, False), 'd': (0x44, False),
        'e': (0x45, False), 'f': (0x46, False), 'g': (0x47, False), 'h': (0x48, False),
        'i': (0x49, False), 'j': (0x4A, False), 'k': (0x4B, False), 'l': (0x4C, False),
        'm': (0x4D, False), 'n': (0x4E, False), 'o': (0x4F, False), 'p': (0x50, False),
        'q': (0x51, False), 'r': (0x52, False), 's': (0x53, False), 't': (0x54, False),
        'u': (0x55, False), 'v': (0x56, False), 'w': (0x57, False), 'x': (0x58, False),
        'y': (0x59, False), 'z': (0x5A, False), '0': (0x30, False), '1': (0x31, False),
        '2': (0x32, False), '3': (0x33, False), '4': (0x34, False), '5': (0x35, False),
        '6': (0x36, False), '7': (0x37, False), '8': (0x38, False), '9': (0x39, False),
        ' ': (0x20, False), '.': (0xBE, False), ',': (0xBC, False), ';': (0xBA, False),
        '/': (0xBF, False), '[': (0xDB, False), ']': (0xDD, False), '\\': (0xDC, False),
        '-': (0xBD, False), '=': (0xBB, False), '`': (0xC0, False), "'": (0xDE, False),
        '\n': (0x0D, False), '\t': (0x09, False),
        '{': (0xDB, True), '}': (0xDD, True), '_': (0xBD, True), '%': (0x35, True),
        '!': (0x31, True), '@': (0x32, True), '#': (0x33, True), '$': (0x34, True),
        '^': (0x36, True), '&': (0x37, True), '*': (0x38, True), '(': (0x39, True),
        ')': (0x30, True), '+': (0xBB, True), '|': (0xDC, True), ':': (0xBA, True),
        '"': (0xDE, True), '<': (0xBC, True), '>': (0xBE, True), '?': (0xBF, True),
        '~': (0xC0, True)
    }

    def press_key(vk_code, shift=False):
        if shift:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        win32api.keybd_event(vk_code, 0, 0, 0)
        if delay:
            high_precision_sleep(key_hold_time)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        if shift:
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

    for char in text:
        lower_char = char.lower()
        if lower_char in char_to_vk:
            vk_code, shift = char_to_vk[lower_char]
            if char.isupper():
                shift = True
            press_key(vk_code, shift)
        else:
            print(f"Character '{char}' not supported")
        if delay:
            high_precision_sleep(delay)


def get_mouse_xy():
    x, y = win32api.GetCursorPos()
    return x, y


def base62_hash(data):
    return zhmiscellany.string.convert_to_base62(int(int(hashlib.md5(data if isinstance(data, bytes) else str(data).encode()).hexdigest(), 16)**0.5))


def high_precision_sleep(duration):
    start_time = time.perf_counter()
    while True:
        elapsed_time = time.perf_counter() - start_time
        remaining_time = duration - elapsed_time
        if remaining_time <= 0:
            break
        if remaining_time > 0.02:  # Sleep for 5ms if remaining time is greater
            time.sleep(max(remaining_time/2, 0.0001))  # Sleep for the remaining time or minimum sleep interval
        else:
            pass


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        return False


def run_as_admin(keep_console = False):
    if is_admin():
        print("Already running as administrator.")
        return

    # Get the script path
    if getattr(sys, 'frozen', False):
        # If the script is compiled to an EXE
        script_path = sys.executable
        compiled = True
    else:
        # If the script is being run as a .py file
        script_path = sys.argv[0]
        compiled = False

    # Run the script with admin privileges
    params = ' '.join([script_path] + sys.argv[1:])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        if not keep_console:
            die()
        else:
            while True:
                time.sleep(1)

    # Exit the current script after attempting to rerun as admin
    if not keep_console:
        die()
    else:
        while True:
            time.sleep(1)