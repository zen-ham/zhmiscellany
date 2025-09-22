from ._processing_supportfuncs import batch_multiprocess, multiprocess, synchronous_class_multiprocess, ThreadWithResult
import threading, kthread
import traceback
import zhmiscellany.string
import concurrent.futures
import subprocess, zlib, pickle, dill, tempfile, os, base64


def start_daemon(**kwargs):
    thread = threading.Thread(**kwargs)
    thread.daemon = True
    thread.start()
    return thread


def batch_threading(targets, max_threads=None, show_errors=True):
    def execute_target(target):
        try: return target[0](*target[1])
        except Exception:
            if show_errors: print(traceback.format_exc())
            return None

    max_threads = max_threads or len(targets)
    results = [None] * len(targets)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(execute_target, t): i for i, t in enumerate(targets)}
        for f in concurrent.futures.as_completed(futures):
            try: results[futures[f]] = f.result()
            except Exception: results[futures[f]] = None
    return results


def batch_threading_gen(targets, max_threads=None, show_errors=True):
    def execute_target(target):
        try: return target[0](*target[1])
        except Exception:
            if show_errors: print(traceback.format_exc())
            return None

    max_threads = max_threads or len(targets)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(execute_target, t) for t in targets]
        for f in concurrent.futures.as_completed(futures):
            try: yield f.result()
            except Exception: yield None


def batch_multiprocess_threaded(targets_and_args, disable_warning=False, killable=False, daemon=False):
    if killable:
        thread_method = kthread.KThread
    else:
        thread_method = threading.Thread
    t = thread_method(target=batch_multiprocess, args=(targets_and_args, disable_warning))
    if daemon:
        t.daemon = True
    t.start()
    return t


def multiprocess_threaded(target, args=(), disable_warning=False, killable=False, daemon=False):
    return batch_multiprocess_threaded([(target, args)], disable_warning=False, killable=False, daemon=False)


def raw_multiprocess(func, args=(), fileless=True):
    cap_string = b'|'+bytes(zhmiscellany.string.get_universally_unique_string(), 'u8')+b'|'
    code = \
'''import os, dill, zlib, sys, pickle, traceback, psutil, signal
cwd = '''+repr(os.getcwd())+'''
host_pid = {os.getpid()}
os.chdir(os.path.dirname(cwd))
func = dill.loads(zlib.decompress('''+repr(zlib.compress(dill.dumps(func), 9))+'''))
args_list = dill.loads(zlib.decompress('''+repr(zlib.compress(dill.dumps(args), 9))+f'''))
if __name__ == "__main__":
    data = [None, None]
    def sync_host_alive_state():
        while True:
            if psutil.pid_exists(host_pid):
                time.sleep(0.1)
                continue
            os.kill(os.getpid(), signal.SIGTERM)
    b = threading.Thread(target=sync_host_alive_state)
    b.daemon = True
    b.start()
    computed = False
    try:
        result = func(*args_list)
        computed = True
    except:
        data[0] = traceback.format_exc()
    if computed:
        data[1] = result
        del result
    try:
        pickled = pickle.dumps(data, protocol=5)
    except:
        try:
            pickled = dill.dumps(data, protocol=5)
        except:
            pickled = pickle.dumps([1, None], protocol=5)
    del data
    compressed = zlib.compress(pickled, 9);del pickled
    sys.stdout.buffer.write({repr(cap_string)} + compressed + {repr(cap_string)})
    sys.stdout.buffer.flush()
'''
    if not fileless:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
            
            try:
                result = subprocess.run(
                    ["python", temp_path],
                    capture_output=True,  # Capture stdout and stderr
                    text=False
                )
            except:
                result = None
    else:  # multiprocessing doesn't support this >:(
        result = subprocess.run(
            ["python", '-c', code],
            capture_output=True,  # Capture stdout and stderr
            text=False
        )
    if result is None:
        raise Exception('Critical error when trying to execute process.')
    if not fileless:
        os.unlink(temp_path)
    raw = result.stdout + result.stderr
    # very annoying fix for ansi code at the start and end of the output, also a fix for if the passed functions have their own console output
    try:
        raw = raw.split(cap_string)[1].split(cap_string)[0]
    except:
        raise Exception(f'Critical error in process:\n{raw}')
    
    try:
        decompressed = zlib.decompress(raw)
    except Exception as e:
        print(raw)
        raise e

    try:
        var = pickle.loads(decompressed)
    except:
        var = dill.loads(decompressed)

    if var[0] is None:
        results = var[1]
    elif var[0] == 1:
        raise Exception('The result of the function you passed from at least one process was unpickable, even with dill. ')
    else:
        raise Exception(f'An error occurred in the function you passed:\n\n{var[0]}')

    return results


def raw_continuous_multiprocess(input_class, args=(), fileless=True, cleanup_file=True):
    cap_string = b'|' + bytes(zhmiscellany.string.get_universally_unique_string(), 'u8') + b'|'
    block_header_string = b'|' + bytes(zhmiscellany.string.get_universally_unique_string(), 'u8') + b'|'
    completion_marker = b'|' + bytes(zhmiscellany.string.get_universally_unique_string(), 'u8') + b'|'
    # convert markers to strings (they are ASCII-safe)
    cap_str = cap_string.decode('utf-8')
    block_header_str = block_header_string.decode('utf-8')
    completion_marker_str = completion_marker.decode('utf-8')
    marker_prefix = block_header_str + cap_str
    
    code = f'''
import os, dill, zlib, sys, pickle, traceback, base64, threading, psutil, time, signal
cwd = {repr(os.getcwd())}
host_pid = {os.getpid()}
os.chdir(os.path.dirname(cwd))
env = os.environ.copy()
env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
if __name__=="__main__":
    data = [None, None]
    def sync_host_alive_state():
        while True:
            if psutil.pid_exists(host_pid):
                time.sleep(0.1)
                continue
            os.kill(os.getpid(), signal.SIGTERM)
    b = threading.Thread(target=sync_host_alive_state)
    b.daemon = True
    b.start()
    def write_out(data):
        try:
            pickled = pickle.dumps(data, protocol=5)
        except:
            try:
                pickled = dill.dumps(data, protocol=5)
            except:
                pickled = pickle.dumps([1, None], protocol=5)
        compressed = zlib.compress(pickled, 9)
        encoded = base64.b64encode(compressed).decode('utf-8')
        print({repr(block_header_str)} + {repr(cap_str)} + encoded + {repr(cap_str)} + '\\n', flush=True, end='')
    computed = False
    try:
        cls = dill.loads(zlib.decompress({repr(zlib.compress(dill.dumps(input_class), 9))}))
        args_list = dill.loads(zlib.decompress({repr(zlib.compress(dill.dumps(args), 9))}))
        computed = True
    except:
        data[0] = traceback.format_exc()
    if computed:
        try:
            cls = cls(*args_list)
            computed = True
        except:
            data[0] = traceback.format_exc()
    if computed:
        computed = True
        try:
            threads = []
            for result in cls.output():
                data[1] = result
                t = threading.Thread(target=write_out, args=(data,))
                threads.append(t)
                t.start()
            for thread in threads:
                thread.join()
        except:
            data[1] = None
            data[0] = traceback.format_exc()
            write_out(data)
            computed = False
        if computed:
            data[1] = {repr(completion_marker_str)}
            write_out(data)
    else:
        write_out(data)
'''
    if not fileless:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        proc = subprocess.Popen(["python", temp_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1)
    else:
        proc = subprocess.Popen(["python", "-c", code],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1)
    
    def cleanup():
        if not fileless:
            if cleanup_file:
                os.unlink(temp_path)
    
    # Read output line-by-line so results are yielded as soon as they're printed.
    for line in proc.stdout:
        line = line.strip()
        if not (line.startswith(marker_prefix) and line.endswith(cap_str)):
            continue
        encoded = line[len(marker_prefix):-len(cap_str)]
        try:
            compressed = base64.b64decode(encoded)
            decompressed = zlib.decompress(compressed)
        except Exception as e:
            raise Exception("Error decoding output") from e
        try:
            var = pickle.loads(decompressed)
        except:
            var = dill.loads(decompressed)
        if var[0] is not None:
            if var[0] == 1:
                raise Exception("Result unpickable even with dill.")
            else:
                raise Exception(f"Error in function:\n\n{var[0]}")
        if var[1] == completion_marker_str:
            proc.stdout.close()
            proc.wait()
            cleanup()
            return
        else:
            yield var[1]
    proc.stdout.close()
    proc.wait()
    cleanup()


class thread_join_return(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    # A custom 'join' that also returns the value
    def join(self, *args):
        super().join(*args)
        return self._return