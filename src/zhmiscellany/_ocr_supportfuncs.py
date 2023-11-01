import sys
import time
import zhmiscellany.fileio
import zhmiscellany.string
import os
import threading
from PIL import Image
import pytesseract


def count_threads_by_string(string):
    count = 0
    for thread in threading.enumerate():
        if isinstance(thread, threading.Thread) and string in thread.name:
            count += 1
    return count


def print_str_if(string, print_it):
    if print_it:
        sys.stdout.write(string+'\n')


def set_tesseract_path():
    anyway = False
    if getattr(sys, 'frozen', False):
        # we are running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # we are running in normal Python environment
        base_path = os.path.dirname(__file__)
        state_path = os.path.join(base_path, '_state.py')
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = f.read()
            if state == '_state=0':
                with open(state_path, 'w') as f:
                    f.write('_state=1')
                anyway = True

    cwd = os.getcwd()
    if (not os.path.exists(os.path.join(base_path, 'resources'))) or anyway:
        if os.path.exists(os.path.join(base_path, 'resources')):
            zhmiscellany.fileio.remove_folder(os.path.join(base_path, 'resources'))
        os.chdir(base_path)
        from ._py_resources import gen
        gen()
        os.chdir(cwd)
    tesseract_path = os.path.join(base_path, 'resources', 'tesseract')
    pytesseract.pytesseract.tesseract_cmd = f'{tesseract_path}\\tesseract.exe'


def ocr(image):
    if type(image) == str:
        try:
            if '.ico' in image:
                ico_file = Image.open(image)
                png_file = ico_file.convert("RGBA")
                text = pytesseract.image_to_string(png_file)
            else:
                text = pytesseract.image_to_string(Image.open(image))
            #print_str_if(f'succeeded {image_path}', _batch_ocr_use_console)
            return text
        except Exception as e:
            raise f'\nFailed to run OCR on file {image}\n\n{e}\n'
    else:
        return pytesseract.image_to_string(image)


def s_ocr(image, _batch_ocr_use_console):
    if type(image) == str:
        try:
            if '.ico' in image:
                ico_file = Image.open(image)
                png_file = ico_file.convert("RGBA")
                text = pytesseract.image_to_string(png_file)
            else:
                text = pytesseract.image_to_string(Image.open(image))
            print_str_if(f'succeeded {image}', _batch_ocr_use_console)
            return text
        except Exception as e:
            print_str_if(f'\nfailed {image}\n\n{e}\n', _batch_ocr_use_console)
            return ''
    else:
        return pytesseract.image_to_string(image)


def l_ocr(image, thread_string, pos, _batch_ocr_use_console):
    if type(image) == str:
        _batch_ocr_cache_dict[thread_string][image] = s_ocr(image, _batch_ocr_use_console)
    else:
        _batch_ocr_cache_dict[thread_string][pos] = s_ocr(image, _batch_ocr_use_console)


_batch_ocr_cache_dict = {}
_ocr_thread_group = zhmiscellany.string.get_universally_unique_string()
set_tesseract_path()


def batch_ocr(images, threads=10, prints=False):
    global _batch_ocr_cache_dict
    _batch_ocr_use_console = prints
    thread_string = zhmiscellany.string.get_universally_unique_string()
    _batch_ocr_cache_dict[thread_string] = {}
    l_images = images[:]
    while len(l_images) > 0:
        while count_threads_by_string(_ocr_thread_group) < threads:
            image = l_images.pop()
            pos = len(l_images)
            threading.Thread(target=l_ocr, args=(image, thread_string, pos, _batch_ocr_use_console), name=f'{_ocr_thread_group}_{thread_string}_{zhmiscellany.string.get_universally_unique_string()}').start()
            if len(l_images) < 1:
                break
        time.sleep(0.1)

    while count_threads_by_string(thread_string) or thread_string not in _batch_ocr_cache_dict:
        time.sleep(0.1)

    output_dict = {}
    for each in _batch_ocr_cache_dict[thread_string]:
        output_dict[each] = _batch_ocr_cache_dict[thread_string][each]
    _batch_ocr_cache_dict.pop(thread_string)

    return output_dict
