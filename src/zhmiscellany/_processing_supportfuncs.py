# these lines are purposefully the first thing to run when zhmiscellany is imported
import threading, logging, os, inspect
import ray

os.environ["RAY_DISABLE_LOGGING"] = "1"

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
            if __file__ != file_name:
                chain.append(file_name)
        frame = frame.f_back
    return chain[::-1]


cause_files = get_import_chain()

code = ''
for file in cause_files:
    if os.path.exists(file):
        with open(file, 'r', encoding='u8', errors='ignore') as f:
            code += f.read()

_ray_init_thread = threading.Thread()  # initialize variable to completed thread
_ray_init_thread.start()

_ray_state = 'disabled'
cause_strings = [
    'processing.multiprocess(',
    'processing.batch_multiprocess(',
    'processing.synchronous_class_multiprocess(',
    'processing.multiprocess_threaded(',
    'processing.batch_multiprocess_threaded(',
]

if any([i in code for i in cause_strings]) or os.environ.get('zhmiscellany_init_ray') == 'force':
    ray_init()


class ThreadWithResult(threading.Thread):
    def __init__(self, target, args, **kwargs):
        super().__init__()
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self.result = None

    def run(self):
        if self._target:
            self.result = self._target(*self._args, **self._kwargs)


def batch_multiprocess(targets_and_args, max_retries=0, expect_crashes=False, disable_warning=False):
    if _ray_state == 'disabled':
        if not disable_warning:
            logging.warning("zhmiscellany didn't detect that you were going to be using multiprocessing functions, and ray was not initialized preemptively.\n\
All this means is that ray will have to be initialized now and the this call to multiprocessing will have to wait a few (around 4) seconds.\n\
If you want to avoid this in the future you can set `os.environ['zhmiscellany_init_ray'] = 'force'` BEFORE importing zhmiscellany, or you can pass disable_warning=True to this function call.")
        ray_init()
    if _ray_state == 'starting':
        if not disable_warning:
            logging.warning("You called multiprocessing early enough that ray is not fully initialized yet.\n\
All this means is that ray is still being initialized and this call to multiprocessing will have to wait a few seconds.\n\
If you want to avoid this in the future and wait until ray is ready you can add this line just after importing zhmiscellany: (Or you can pass disable_warning=True to this function call)\n\
from zhmiscellany._processing_supportfuncs import _ray_init_thread; _ray_init_thread.join()")
    _ray_init_thread.join()
    
    if not expect_crashes:
        @ray.remote(max_retries=max_retries)
        def worker(func, *args):
            return func(*args)
        
        futures = [worker.remote(func, *args) for func, args in targets_and_args]
        results = ray.get(futures)
        return results
    else:
        def wrap_exception(task, disable_warning, max_retries):
            try:
                result = multiprocess(*task, disable_warning=disable_warning, max_retries=max_retries)
                return result
            except ray.exceptions.WorkerCrashedError:
                return None
        threads = []
        for task in targets_and_args:
            t = ThreadWithResult(
                target=wrap_exception,
                args=(task, disable_warning, max_retries),
            )
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        results = [t.result for t in threads]
        return results

def multiprocess(target, args=(), max_retries=0, disable_warning=False):
    return batch_multiprocess([(target, args)], disable_warning=disable_warning, max_retries=max_retries)[0]


class RayActorWrapper:
    def __init__(self, actor_instance):
        self._actor = actor_instance
        
        ray.get(self._actor._ready.remote())
    
    def __getattr__(self, name):
        # When you access an attribute, assume it's a remote method.
        remote_method = getattr(self._actor, name)
        if not callable(remote_method):
            # If it's not callable, try to get its value.
            return ray.get(remote_method)
        
        # Return a callable that wraps the remote method.
        def wrapper(*args, **kwargs):
            # Call the remote method and get the result.
            result_ref = remote_method.remote(*args, **kwargs)
            return ray.get(result_ref)
        
        return wrapper


def synchronous_class_multiprocess(cls, *args, disable_warning=False, **kwargs):
    if _ray_state == 'disabled':
        if not disable_warning:
            logging.warning("zhmiscellany didn't detect that you were going to be using multiprocessing functions, and ray was not initialized preemptively.\n\
    All this means is that ray will have to be initialized now and the this call to multiprocessing will have to wait a few (around 4) seconds.\n\
    If you want to avoid this in the future you can set `os.environ['zhmiscellany_init_ray'] = 'force'` BEFORE importing zhmiscellany, or you can pass disable_warning=True to this function call.")
        ray_init()
    if _ray_state == 'starting':
        if not disable_warning:
            logging.warning("You called multiprocessing early enough that ray is not fully initialized yet.\n\
    All this means is that ray is still being initialized and this call to multiprocessing will have to wait a few seconds.\n\
    If you want to avoid this in the future and wait until ray is ready you can add this line just after importing zhmiscellany: (Or you can pass disable_warning=True to this function call)\n\
    from zhmiscellany._processing_supportfuncs import _ray_init_thread; _ray_init_thread.join()")
    _ray_init_thread.join()
    
    def _ready(self):
        return True
    
    cls._ready = _ready
    
    remote_cls = ray.remote(cls)
    actor_instance = remote_cls.remote(*args, **kwargs)
    return RayActorWrapper(actor_instance)