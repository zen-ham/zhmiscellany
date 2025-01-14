import os, signal, importlib
import zhmiscellany.math
import zhmiscellany.string
import zhmiscellany.processing
import zhmiscellany.mousekb
import zhmiscellany.fileio
import time, hashlib, ctypes
import keyboard
import subprocess

# support backwards compatibility
click_pixel = zhmiscellany.mousekb.click_pixel
type_string = zhmiscellany.mousekb.type_string
scroll = zhmiscellany.mousekb.scroll
get_mouse_xy = zhmiscellany.mousekb.get_mouse_xy
KEY_CODES = zhmiscellany.mousekb.KEY_CODES


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


def base62_hash(anything):
    return zhmiscellany.string.convert_to_base62(int(int(hashlib.md5(anything if isinstance(anything, bytes) else str(anything).encode()).hexdigest(), 16)**0.5))


def md5_int_hash(anything):
    return int(hashlib.md5(anything if isinstance(anything, bytes) else str(anything).encode()).hexdigest(), 16)


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


def die_on_key(key='f9', show_message=False):
    def _die_on_key(key):
        keyboard.wait(key)
        if show_message:
            print("Stopping the process because exit key was pressed.")
        die()
    zhmiscellany.processing.start_daemon(target=_die_on_key, args=(key,))


temp_folder = os.popen(r'echo %TEMP%').read().replace('\n', '')


def obfuscate_python(python_code_string, remove_prints=True, remove_comments=True):
    obf = python_code_string
    if remove_prints or remove_comments:
        lines = obf.split('\n')
        for i, line in enumerate(lines):
            if line.replace(' ', '').startswith('print('):
                j = 0
                for j, char in enumerate(line):
                    if char != ' ':
                        break
                lines[i] = f'{" "*j}pass'
        obf = '\n'.join(lines)

    return obf