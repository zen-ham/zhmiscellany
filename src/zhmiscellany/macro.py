import math
import random
import threading

from ._misc_supportfuncs import move_mouse, mouse_down, mouse_up
import zhmiscellany.misc
import zhmiscellany.math
import zhmiscellany.string
import zhmiscellany.processing
import win32api, win32con, ctypes

import keyboard, kthread

import time


def click_pixel(x=None, y=None, click_duration=None, right_click=False, middle_click=False, shift=False, ctrl=False, act_start=True, act_end=True, click_end_duration=None, double_click=False, animation_time=None, animation_fps=60, animation_easing=True, relative=False, ensure_movement=True, pre_click_duration=None, pre_click_wiggle=False):
    if right_click and middle_click:
        raise Exception('Both right click and middle click were set to true. Make sure just one is set to true at a time, or neither.')
    if type(x) != tuple and type(x) != list:
        if (x is None and y is not None) or (x is not None and y is None):
            raise Exception('x and y need to be either both defined or neither defined, or x needs to be a tuple or list, with 2 elements. you passed one and not the other and x was not such a tuple.')
    else:
        y = x[1]
        x = x[0]

    if animation_time:
        mxy = get_mouse_xy()

    # if relative:
    #     cx, cy = mxy
    #     x += cx
    #     y += cy
    keys_down = []

    if animation_time:
        start = mxy
        end = (x, y)
        num_points = animation_fps*animation_time  # 60 fps animation
        num_points += 2  # don't need start and end points
        num_points = math.ceil(num_points)
        if animation_easing:
            animation_points = zhmiscellany.math.generate_eased_points(start, end, num_points)
        else:
            animation_points = zhmiscellany.math.generate_linear_points(start, end, num_points)

        if relative:
            temp = []
            for i, point in enumerate(animation_points):
                if i == 0:
                    temp.append(tuple(a - b for a, b in zip(animation_points[i], start)))
                    continue

                relative_point = tuple(a - b for a, b in zip(animation_points[i], animation_points[i-1]))

                temp.append(relative_point)
            animation_points = temp

        animation_points.pop()  # remove start and end
        animation_points.pop(0)
        for point in animation_points:
            click_pixel((round(point[0]), round(point[1])), act_start=False, act_end=False, click_end_duration=1/animation_fps, relative=relative)

    if ctrl:
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        keys_down.append(win32con.VK_CONTROL)

    if shift:
        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        keys_down.append(win32con.VK_SHIFT)

    if x is not None and y is not None:
        if not relative:
            cx = x+1
            cy = y+1
        else:
            cx = x
            cy = y
        if ensure_movement:
            limit = 2**5
            move_mouse(cx, cy, relative=relative)
            for i in range(limit):
                if get_mouse_xy() != (x, y):
                    move_mouse(cx, cy, relative=relative)
                else:
                    break
        else:
            move_mouse(cx, cy, relative=relative)

    if pre_click_duration:
        if pre_click_wiggle:
            num_wiggle = round(animation_fps * pre_click_duration)
            for i in range(num_wiggle):
                click_pixel(cx+((random.randint(0, 1)*2)-1), cy+((random.randint(0, 1)*2)-1), act_start=False, act_end=False, click_end_duration=1 / animation_fps)
        else:
            zhmiscellany.misc.high_precision_sleep(pre_click_duration)

    if middle_click:
        if act_start:
            mouse_down(3)
        if click_duration:
            zhmiscellany.misc.high_precision_sleep(click_duration)
        if act_end:
            mouse_up(3)
    elif right_click:
        if act_start:
            mouse_down(2)
        if click_duration:
            zhmiscellany.misc.high_precision_sleep(click_duration)
        if act_end:
            mouse_up(2)
    else:
        if act_start:
            mouse_down(1)
        if click_duration:
            zhmiscellany.misc.high_precision_sleep(click_duration)
        if act_end:
            mouse_up(1)

    for key in keys_down:
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

    if click_end_duration:
        zhmiscellany.misc.high_precision_sleep(click_end_duration)

    if double_click:
        click_pixel(x, y, click_duration, right_click, shift, ctrl, act_start, act_end, middle_click, click_end_duration, pre_click_duration=pre_click_duration, pre_click_wiggle=pre_click_wiggle)


def press_key_directinput(key, shift=False, act_start=True, act_end=True, key_hold_time=0):
    import pydirectinput
    pydirectinput.PAUSE = 0
    pydirectinput.FAILSAFE = False
    if shift: pydirectinput.keyDown('shift')
    if act_start: pydirectinput.keyDown(key)
    if key_hold_time: zhmiscellany.misc.high_precision_sleep(key_hold_time)
    if act_end: pydirectinput.keyUp(key)
    if shift: pydirectinput.keyUp('shift')


def press_key(vk_code, shift=False, act_start=True, act_end=True, key_hold_time=0):
    if shift:
        win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
    if act_start:
        win32api.keybd_event(vk_code, 0, 0, 0)  # press
    if key_hold_time:
        zhmiscellany.misc.high_precision_sleep(key_hold_time)
    if act_end:
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)  # release
    if shift:
        win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)


def type_string(text=None, delay=None, key_hold_time=None, vk_codes=None, combine=False):
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

    if text:
        for char in text:
            lower_char = char.lower()
            if lower_char in char_to_vk:
                vk_code, shift = char_to_vk[lower_char]
                if char.isupper():
                    shift = True
                press_key(vk_code, shift, act_end=not combine, key_hold_time=key_hold_time)
            else:
                print(f"Character '{char}' not supported")
            if delay:
                zhmiscellany.misc.high_precision_sleep(delay)
        if combine:
            key_hold_time = 0  # release all keys at the same time
            for char in text:
                lower_char = char.lower()
                if lower_char in char_to_vk:
                    vk_code, shift = char_to_vk[lower_char]
                    if char.isupper():
                        shift = True
                    press_key(vk_code, shift, act_start=False, act_end=True, key_hold_time=key_hold_time)
                else:
                    print(f"Character '{char}' not supported")
    if vk_codes:
        for vk_code in vk_codes:
            press_key(vk_code, False, act_end=not combine, key_hold_time=key_hold_time)
            if delay:
                zhmiscellany.misc.high_precision_sleep(delay)
        if combine:
            key_hold_time = 0  # release all keys at the same time
            for vk_code in vk_codes:
                press_key(vk_code, False, act_start=False, act_end=True, key_hold_time=key_hold_time)


def scroll(amount, delay=None):
    def raw_scroll(amount):
        # Constants for mouse input
        INPUT_MOUSE = 0
        MOUSEEVENTF_WHEEL = 0x0800

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_ulong),
                ("mi", MOUSEINPUT),
            ]

        amount = amount * 120
        # Prepare the input structure
        extra = ctypes.c_ulong(0)
        x = INPUT(
            type=INPUT_MOUSE,
            mi=MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=amount,
                dwFlags=MOUSEEVENTF_WHEEL,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            ),
        )
        # Send the input
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    if delay is None:
        raw_scroll(amount)
    else:
        direction = 1 if amount > 0 else -1
        amount = amount*direction
        for _ in range(amount):
            raw_scroll(amount)
            zhmiscellany.misc.high_precision_sleep(delay/amount)


def get_mouse_xy():
    x, y = win32api.GetCursorPos()
    return x, y


def get_mouse_buttons():
    """Returns a list of booleans [M1, M2, M3] indicating which mouse buttons are held down."""
    VK_LBUTTON = 0x01  # Left mouse button (M1)
    VK_RBUTTON = 0x02  # Right mouse button (M2)
    VK_MBUTTON = 0x04  # Middle mouse button (M3)
    
    GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
    
    return [
        bool(GetAsyncKeyState(VK_LBUTTON) & 0x8000),
        bool(GetAsyncKeyState(VK_RBUTTON) & 0x8000),
        bool(GetAsyncKeyState(VK_MBUTTON) & 0x8000)
    ]


_last_press_time_map = {} # Stores the last press timestamp for each key

def better_wait_for(key):
    key_name = key.lower()
    press_event = threading.Event() # Event to signal when the key is pressed
    _last_press_time_map.setdefault(key_name, 0) # Initialize last press time for this key

    def _on_key_event(e):
        if e.name == key_name and e.event_type == keyboard.KEY_DOWN:
            current_time = time.time()
            _last_press_time_map[key_name] = current_time # Update last press time
            press_event.set() # Signal that the key was pressed

    hook_id = keyboard.on_press(_on_key_event) # Register the raw key press listener
    press_event.wait() # Block execution until the press_event is set
    keyboard.unhook(hook_id) # Clean up the listener after key is detected


def toggle_function(func, key='f8', blocking=True):
    def atom():
        while True:
            better_wait_for(key)
            t = kthread.KThread(target=func)
            t.start()
            better_wait_for(key)
            t.kill()
    if blocking:
        atom()
    else:
        t = threading.Thread(target=atom)
        t.start()
        return t


KEY_CODES = {
    'None': 0,
    'LeftMouseButton': 1,
    'RightMouseButton': 2,
    'ControlBreak': 3,
    'MiddleMouseButton': 4,
    'X1MouseButton': 5,
    'X2MouseButton': 6,
    'Backspace': 8,
    'Tab': 9,
    'Clear': 12,
    'Enter': 13,
    'Shift': 16,
    'Ctrl': 17,
    'Alt': 18,
    'Pause': 19,
    'CapsLock': 20,
    'Escape': 27,
    'Space': 32,
    'PageUp': 33,
    'PageDown': 34,
    'End': 35,
    'Home': 36,
    'LeftArrow': 37,
    'UpArrow': 38,
    'RightArrow': 39,
    'DownArrow': 40,
    'Select': 41,
    'Print': 42,
    'Execute': 43,
    'PrintScreen': 44,
    'Ins': 45,
    'INS': 45,
    'Delete': 46,
    'Help': 47,
    'Key0': 48,
    'Key1': 49,
    'Key2': 50,
    'Key3': 51,
    'Key4': 52,
    'Key5': 53,
    'Key6': 54,
    'Key7': 55,
    'Key8': 56,
    'Key9': 57,
    'A': 65,
    'B': 66,
    'C': 67,
    'D': 68,
    'E': 69,
    'F': 70,
    'G': 71,
    'H': 72,
    'I': 73,
    'J': 74,
    'K': 75,
    'L': 76,
    'M': 77,
    'N': 78,
    'O': 79,
    'P': 80,
    'Q': 81,
    'R': 82,
    'S': 83,
    'T': 84,
    'U': 85,
    'V': 86,
    'W': 87,
    'X': 88,
    'Y': 89,
    'Z': 90,
    'LeftWindowsKey': 91,
    'RightWindowsKey': 92,
    'Application': 93,
    'Sleep': 95,
    'NumpadKey0': 96,
    'NumpadKey1': 97,
    'NumpadKey2': 98,
    'NumpadKey3': 99,
    'NumpadKey4': 100,
    'NumpadKey5': 101,
    'NumpadKey6': 102,
    'NumpadKey7': 103,
    'NumpadKey8': 104,
    'NumpadKey9': 105,
    'Multiply': 106,
    'Add': 107,
    'Separator': 108,
    'Subtract': 109,
    'Decimal': 110,
    'Divide': 111,
    'F1': 112,
    'F2': 113,
    'F3': 114,
    'F4': 115,
    'F5': 116,
    'F6': 117,
    'F7': 118,
    'F8': 119,
    'F9': 120,
    'F10': 121,
    'F11': 122,
    'F12': 123,
    'F13': 124,
    'F14': 125,
    'F15': 126,
    'F16': 127,
    'F17': 128,
    'F18': 129,
    'F19': 130,
    'F20': 131,
    'F21': 132,
    'F22': 133,
    'F23': 134,
    'F24': 135,
    'F25': 136,
    'NumLock': 144,
    'ScrollLock': 145,
    'LeftShift': 160,
    'RightShift': 161,
    'LeftControl': 162,
    'RightControl': 163,
    'LeftAlt': 164,
    'RightAlt': 165,
    'BrowserBack': 166,
    'BrowserRefresh': 168,
    'BrowserStop': 169,
    'BrowserSearch': 170,
    'BrowserFavorites': 171,
    'BrowserHome': 172,
    'VolumeMute': 173,
    'VolumeDown': 174,
    'VolumeUp': 175,
    'NextTrack': 176,
    'PreviousTrack': 177,
    'StopMedia': 178,
    'PlayMedia': 179,
    'StartMailKey': 180,
    'SelectMedia': 181,
    'StartApplication1': 182,
    'StartApplication2': 183
}
