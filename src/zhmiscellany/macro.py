from ._misc_supportfuncs import move_mouse, mouse_down, mouse_up, get_mouse_xy
import sys

IS_WINDOWS = sys.platform == "win32"

_last_press_time_map = {}  # Stores the last press timestamp for each key

def click_pixel(x=None, y=None, click_duration=None, right_click=False, middle_click=False, shift=False, ctrl=False, act_start=True, act_end=True, click_end_duration=None, double_click=False, animation_time=None, animation_fps=60, animation_easing=True, relative=False, ensure_movement=True, pre_click_duration=None, pre_click_wiggle=True, click=True):
    import random
    import math
    import zhmiscellany.math
    if IS_WINDOWS:
        import win32api
        import win32con
        import ctypes
    
    if not click:
        act_start=False;act_end=False
    if right_click and middle_click:
        raise Exception('Both right click and middle click were set to true. Make sure just one is set to true at a time, or neither.')
    if type(x) != tuple and type(x) != list:
        if (x is None and y is not None) or (x is not None and y is None):
            raise Exception('x and y need to be either both defined or neither defined, or x needs to be a tuple or list, with 2 elements. you passed one and not the other and x was not such a tuple.')
    else:
        y = x[1]
        x = x[0]

    def stochastic_round(val):
        negative = val < 0
        if negative:
            val = val * -1
        floor = int(val)
        out = floor + (random.random() < (val - floor))
        if negative:
            out = out * -1
        return out

    if type(x) == float:
        x = stochastic_round(x)

    if type(y) == float:
        y = stochastic_round(y)

    keys_down = []

    if animation_time:
        def ease_in_out_sine(t: float) -> float:
            return 0.5 * (1 - math.cos(math.pi * t))

        def generate_movement_offsets(total_dx: int, total_dy: int, n_steps: int, ease: bool = True) -> list[tuple[int, int]]:
            if n_steps <= 0:
                return []

            offsets = []

            current_actual_x = 0
            current_actual_y = 0

            for i in range(n_steps):
                t = (i + 1) / n_steps

                if ease:
                    fraction_of_total_movement = ease_in_out_sine(t)
                else:
                    fraction_of_total_movement = t

                target_x = round(total_dx * fraction_of_total_movement)
                target_y = round(total_dy * fraction_of_total_movement)

                dx = int(target_x - current_actual_x)
                dy = int(target_y - current_actual_y)

                offsets.append((dx, dy))

                current_actual_x += dx
                current_actual_y += dy

            return offsets

        mxy = get_mouse_xy()
        start = mxy
        end = (x, y)
        num_points = animation_fps*animation_time  # 60 fps animation
        if not relative:
            num_points += 2  # don't need start and end points
        num_points = math.ceil(num_points)
        if animation_easing:
            if not relative:
                animation_points = zhmiscellany.math.generate_eased_points(start, end, num_points)
            else:
                animation_points = generate_movement_offsets(end[0], end[1], num_points)
        else:
            if not relative:
                animation_points = zhmiscellany.math.generate_linear_points(start, end, num_points)
            else:
                animation_points = generate_movement_offsets(end[0], end[1], num_points, ease=False)

        # remove start and end
        if not relative:
            animation_points.pop(0)
            animation_points.pop()
        for point in animation_points:
            click_pixel((round(point[0]), round(point[1])), act_start=False, act_end=False, click_end_duration=1/animation_fps, relative=relative)

    if IS_WINDOWS:
        if ctrl:
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            keys_down.append(win32con.VK_CONTROL)

        if shift:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            keys_down.append(win32con.VK_SHIFT)
    else:
        if ctrl or shift:
            print("Warning: Modifier keys not supported on this platform")

    if x is not None and y is not None:
        if not relative:
            cx = x+1
            cy = y+1
        else:
            cx = x
            cy = y
        limit = 2 ** 5
        if ensure_movement and (not relative):
            move_mouse(cx, cy, relative=relative)
            for i in range(limit):
                if get_mouse_xy() != (x, y):
                    move_mouse(cx, cy, relative=relative)
                else:
                    break
        else:
            if not relative:
                move_mouse(cx, cy, relative=relative)
            else:
                if not (animation_time and relative):
                    targ = tuple(a + b for a, b in zip(get_mouse_xy(), (cx, cy)))
                    move_mouse(cx, cy, relative=relative)
                    if ensure_movement:
                        for i in range(limit):
                            cur_pos = get_mouse_xy()
                            if cur_pos != targ:
                                move_mouse(max(-1, min(1, (targ[0]-cur_pos[0]))), max(-1, min(1, (targ[1]-cur_pos[1]))), relative=relative)
                            else:
                                break

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

    if IS_WINDOWS:
        for key in keys_down:
            win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

    if click_end_duration:
        zhmiscellany.misc.high_precision_sleep(click_end_duration)

    if double_click:
        click_pixel(x, y, click_duration, right_click, shift, ctrl, act_start, act_end, middle_click, click_end_duration, pre_click_duration=pre_click_duration, pre_click_wiggle=pre_click_wiggle)

def press_key_directinput(key, shift=False, act_start=True, act_end=True, key_hold_time=0):
    if not IS_WINDOWS:
        print("press_key_directinput() only supports Windows! Functionality disabled")
        return
        
    import pydirectinput
    import zhmiscellany.misc
    pydirectinput.PAUSE = 0
    pydirectinput.FAILSAFE = False
    if shift: pydirectinput.keyDown('shift')
    if act_start: pydirectinput.keyDown(key)
    if key_hold_time: zhmiscellany.misc.high_precision_sleep(key_hold_time)
    if act_end: pydirectinput.keyUp(key)
    if shift: pydirectinput.keyUp('shift')

def press_key(vk_code, shift=False, act_start=True, act_end=True, key_hold_time=0):
    if not IS_WINDOWS:
        print("press_key() only supports Windows! Functionality disabled")
        return
        
    import win32api
    import win32con
    import zhmiscellany.misc
    
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
    import zhmiscellany.misc
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

def is_key_pressed_async(vk_code):
    """
    Async check if a key is currently pressed
    vk_code: Virtual Key code (e.g., 0x41 for 'A', 0x1B for ESC)
    Returns: True if pressed, False otherwise
    """
    if not IS_WINDOWS:
        print("is_key_pressed_async() only supports Windows! Returning False")
        return False
    import win32api
    import ctypes
    return win32api.GetAsyncKeyState(vk_code) & 0x8000 != 0

def scroll(amount, delay=None, post_scroll_delay=None):
    if not IS_WINDOWS:
        print("scroll() only supports Windows! Functionality disabled")
        return
        
    import zhmiscellany.misc
    import ctypes
    
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
            raw_scroll(direction)
            zhmiscellany.misc.high_precision_sleep(delay/amount)
    if post_scroll_delay:
        zhmiscellany.misc.high_precision_sleep(post_scroll_delay)

def get_mouse_buttons():
    """Returns a list of booleans [M1, M2, M3] indicating which mouse buttons are held down."""
    if not IS_WINDOWS:
        print("get_mouse_buttons() only supports Windows! Returning [False, False, False]")
        return [False, False, False]
        
    import ctypes
    
    VK_LBUTTON = 0x01  # Left mouse button (M1)
    VK_RBUTTON = 0x02  # Right mouse button (M2)
    VK_MBUTTON = 0x04  # Middle mouse button (M3)
    
    GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
    
    return [
        bool(GetAsyncKeyState(VK_LBUTTON) & 0x8000),
        bool(GetAsyncKeyState(VK_RBUTTON) & 0x8000),
        bool(GetAsyncKeyState(VK_MBUTTON) & 0x8000)
    ]


def better_wait_for(key, wait_for_release=False):
    import threading
    import keyboard
    import time

    key_name = key.lower()
    event_signal = threading.Event()  # Event to signal when the key event occurs
    _last_press_time_map.setdefault(key_name, 0)  # Initialize last press time for this key

    def _on_key_event(e):
        if e.name == key_name:
            if wait_for_release and e.event_type == keyboard.KEY_UP:
                event_signal.set()  # Signal that the key was released
            elif not wait_for_release and e.event_type == keyboard.KEY_DOWN:
                current_time = time.time()
                _last_press_time_map[key_name] = current_time  # Update last press time
                event_signal.set()  # Signal that the key was pressed

    # Register the appropriate listener based on wait_for_release
    if wait_for_release:
        hook_id = keyboard.on_release(_on_key_event)
    else:
        hook_id = keyboard.on_press(_on_key_event)

    event_signal.wait()  # Block execution until the event is set
    keyboard.unhook(hook_id)  # Clean up the listener after key is detected

def toggle_function(func, key='f8', blocking=True, hold=False):
    import kthread
    import threading
    # better_wait_for is in the same module, no import needed
    
    def atom(hold):
        while True:
            better_wait_for(key)
            t = kthread.KThread(target=func)
            t.start()
            if not hold:
                better_wait_for(key)
            else:
                better_wait_for(key, wait_for_release=True)
            t.kill()
    if blocking:
        atom(hold)
    else:
        t = threading.Thread(target=atom, args=(hold,))
        t.start()
        return t

def record_actions_to_code(RECORD_MOUSE_MOVEMENT=False, STOP_KEY='f9'):
    import time
    import pynput
    import pyperclip

    # --- Configuration ---
    # Set to True to record every single mouse movement.
    # Set to False to only record mouse position on clicks and drags.

    # --- Global State ---
    events = []
    start_time = None

    # --- Helper Functions ---
    def format_key(key):
        """
        Formats the pynput key object into a string for the generated script.
        Handles cases where modifier keys (like Ctrl) are held down, which can
        prevent the `key.char` attribute from being populated correctly.
        """
        if isinstance(key, pynput.keyboard.Key):
            # Special keys (e.g., Key.shift, Key.ctrl)
            return f"Key.{key.name}"

        if isinstance(key, pynput.keyboard.KeyCode):
            # This is the robust way to handle alphanumeric keys, especially with modifiers.
            # key.char can be None or a control character when Ctrl/Alt are held.
            # key.vk is the virtual key code, which is more reliable.

            # Heuristic for A-Z keys (VK codes on Windows/Linux are often in this range)
            if 65 <= getattr(key, 'vk', 0) <= 90:
                return f"'{chr(key.vk).lower()}'"

            # For other keys, try to use the char if it exists
            if key.char:
                bs = '\\'
                return f"'{key.char.replace(bs, bs + bs + bs)}'"

            # As a fallback for other keys without a char, use the vk
            if hasattr(key, 'vk'):
                return f"pynput.keyboard.KeyCode.from_vk({key.vk})"

        # If it's some other type of key object (less common)
        return str(key)

    def generate_code(events, start_time):
        """
        Generates the Python script from the recorded events and copies it to the clipboard.
        """

        if not events:
            print("No actions were recorded.")
            return

        # Code preamble
        code_lines = [
            "import zhmiscellany",
            "",
            "zhmiscellany.misc.die_on_key('f9')",
            "",
            "m = zhmiscellany.macro.click_pixel",
            "k = zhmiscellany.macro.press_key_directinput",
            "s = zhmiscellany.macro.scroll",
            "sleep = zhmiscellany.misc.high_precision_sleep",
            "click_down_time = 1/30",
            "click_release_time = 1/30",
            "mouse_move_dly = 1/60",
            "key_down_time = 1/30",
            "scroll_dly = 1/30",
            "post_scroll_dly = 1/10",
            "pre_click_duration = 1/30",
            "",
            "pre_click_wiggle = True",
            "",
            "animation_time = 0.1",
            "",
            'print("Replaying actions in 3 seconds...")',
            "sleep(3)",
            ""
        ]

        last_time = start_time
        skip_next = 0
        for i, event in enumerate(events):
            if skip_next:
                skip_next -= 1
                continue
            current_time = event['time']
            try:
                next_event = events[i+1]
            except:
                next_event = None
            delay = current_time - last_time

            action = event['action']

            if action == 'click':
                x, y, button, pressed = event['x'], event['y'], event['button'], event['pressed']
                button_str = f"Button.{button.name}"
                action_str = "press" if pressed else "release"

                replacements = {
                    'right': 'right_click=True, ',
                    'middle': 'middle_click=True, ',
                    'left': '',
                }
                for key, value in replacements.items():
                    if key in button_str:
                        button_str = value
                        break

                replacements = {
                    'press': 'act_end=False, ',
                    'release': 'act_start=False, ',
                }
                for key, value in replacements.items():
                    if key in action_str:
                        action_str = value
                        break

                if next_event and next_event['action'] == 'click' and (next_event['x'], next_event['y']) == (x, y):
                    action_str = ''
                    skip_next = 1

                code_lines.append(f"m(({x}, {y}), {button_str}{action_str}click_duration=click_down_time, click_end_duration=click_release_time, pre_click_duration=pre_click_duration, animation_time=animation_time)")

            elif action == 'move':
                x, y = event['x'], event['y']
                code_lines.append(f"m(({x}, {y}), click_end_duration=mouse_move_dly)")

            elif action == 'scroll':
                x, y, dx, dy = event['x'], event['y'], event['dx'], event['dy']
                j = i
                count = 0
                while True:
                    count += 1
                    j += 1
                    try:
                        t_event = events[j]
                    except:
                        t_event = None
                    if t_event and t_event['action'] == 'scroll' and t_event['dy'] == dy and (t_event['x'], t_event['y']) == (x, y):
                        skip_next += 1
                    else:
                        break
                code_lines.append(f"m(({x}, {y}), click_end_duration=mouse_move_dly)")
                code_lines.append(f"s({dy*count}, scroll_dly, post_scroll_dly)")

            elif action in ('key_press', 'key_release'):
                key = event['key']
                key_str = format_key(key)
                if '.' in key_str:
                    key_str = key_str.split('.')[1]
                replacements = {
                    'ctrl': 'ctrl',
                    'shift': 'shift',
                    'alt': 'alt',
                }
                for key, value in replacements.items():
                    if key in key_str:
                        key_str = value
                        break
                action_str = "press" if action == 'key_press' else "release"

                replacements = {
                    'press': 'act_end=False, ',
                    'release': 'act_start=False, ',
                }
                for key, value in replacements.items():
                    if key in action_str:
                        action_str = value
                        break

                if key_str == STOP_KEY:
                    break

                code_lines.append(f"k('{key_str}', {action_str}key_hold_time=key_down_time)")

            last_time = current_time

        code_lines.append("\nprint('Replay finished.')")

        # Join all lines into a single script
        final_script = "\n".join(code_lines)

        # Print and copy to clipboard
        print("\n" + "=" * 50)
        print("      RECORDING FINISHED - SCRIPT GENERATED")
        print("=" * 50 + "\n")
        print(final_script)
        print("\n" + "=" * 50)

        try:
            pyperclip.copy(final_script)
            print("Script has been copied to your clipboard!")
        except pyperclip.PyperclipException:
            print("Could not copy to clipboard. Please install xclip or xsel on Linux.")
        return final_script

    # --- Pynput Listener Callbacks ---

    def on_move(x, y):
        if RECORD_MOUSE_MOVEMENT:
            events.append({'action': 'move', 'x': x, 'y': y, 'time': time.time()})

    def on_click(x, y, button, pressed):
        events.append({'action': 'click', 'x': x, 'y': y, 'button': button, 'pressed': pressed, 'time': time.time()})

    def on_scroll(x, y, dx, dy):
        events.append({'action': 'scroll', 'x': x, 'y': y, 'dx': dx, 'dy': dy, 'time': time.time()})

    def on_press(key):
        events.append({'action': 'key_press', 'key': key, 'time': time.time()})

    def on_release(key):
        try:
            print(key.name)
            if key.name == STOP_KEY:
                # Stop listeners
                return False
        except:
            pass
        events.append({'action': 'key_release', 'key': key, 'time': time.time()})

    print(f"Press '{STOP_KEY}' to stop recording and generate the script.")
    print("...")

    start_time = time.time()

    # Create and start listeners
    mouse_listener = pynput.mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    keyboard_listener = pynput.keyboard.Listener(on_press=on_press, on_release=on_release)

    mouse_listener.start()
    keyboard_listener.start()

    # Wait for the keyboard listener to stop (on F9 press)
    keyboard_listener.join()

    # Stop the mouse listener explicitly once the keyboard one has finished
    mouse_listener.stop()

    # Generate the replay script
    return generate_code(events, start_time)

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
    'StartApplication2': 183,
    'Equals': 187,
    'Comma': 188,
    'Minus': 189,
}