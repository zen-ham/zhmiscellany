# these lines are purposefully the first thing to run when zhmiscellany is imported
import ray, threading, logging, os, inspect


def ray_init():
    global _ray_init_thread
    _ray_init_thread = threading.Thread(target=_ray_init)
    _ray_init_thread.daemon = True
    _ray_init_thread.start()


def _ray_init():
    global _ray_state
    if _ray_state == 'enabled':
        return
    _ray_state = 'starting'
    try:
        ray.init(logging_level="ERROR")
    except RuntimeError as e:
        if 'ray.init twice by accident' in str(e):
            pass
        else:
            raise e
        
    _ray_state = 'enabled'


def get_import_chain():
    frame = inspect.currentframe()
    chain = []
    while frame:
        file_name = frame.f_code.co_filename
        if frame.f_globals.get('__name__') == '__main__':
            chain.append(file_name)
            break
        if file_name not in chain:
            if os.path.exists(file_name) and __file__ != file_name:
                chain.append(file_name)
        frame = frame.f_back
    return chain[::-1]


cause_files = get_import_chain()

code = ''
for file in cause_files:
    with open(file, 'r', encoding='u8', errors='ignore') as f:
        code += f.read()

_ray_init_thread = None
_ray_state = 'disabled'
cause_strings = ['processing.multiprocess(', 'processing.batch_multiprocess(']

if any([i in code for i in cause_strings]) or os.environ.get('zhmiscellany_init_ray') == 'force':
    ray_init()


def batch_multiprocess(targets_and_args, disable_warning=False):
    if _ray_state == 'disabled':
        if not disable_warning:
            logging.warning("zhmiscellany didn't detect that you were going to be using processing.(batch_)multiprocessing functions, and ray was not initialized preemptively.\n\
All this means is that ray will have to be initialized now and the this call to processing.(batch_)multiprocessing will have to wait a few (around 4) seconds.\n\
If you want to avoid this in the future you can set `os.environ['zhmiscellany_init_ray'] = 'force'` BEFORE importing zhmiscellany, or you can pass disable_warning=True to this function call.")
        ray_init()
    if _ray_state == 'starting':
        if not disable_warning:
            logging.warning("You called processing.(batch_)multiprocessing early enough that ray is not fully initialized yet.\n\
All this means is that ray is still being initialized and this call to processing.(batch_)multiprocessing will have to wait a few seconds.\n\
If you want to avoid this in the future and wait until ray is ready you can add this line just after importing zhmiscellany: (Or you can pass disable_warning=True to this function call)\n\
from zhmiscellany._processing_supportfuncs import _ray_init_thread; _ray_init_thread.join()")
    _ray_init_thread.join()
    
    @ray.remote
    def worker(func, *args):
        return func(*args)
    
    futures = [worker.remote(func, *args) for func, args in targets_and_args]
    results = ray.get(futures)
    return results

def multiprocess(target, args=(), disable_warning=False):
    return batch_multiprocess([(target, args)], disable_warning=disable_warning)[0]