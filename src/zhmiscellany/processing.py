from ._processing_supportfuncs import batch_multiprocess, multiprocess
import threading, kthread
import traceback
import zhmiscellany.string
import concurrent.futures
import types, sys, subprocess, zlib, pickle, dill, tempfile


def start_daemon(**kwargs):
    thread = threading.Thread(**kwargs)
    thread.daemon = True
    thread.start()
    return thread


def batch_threading(targets, max_threads, show_errors=True):
    def execute_target(target):
        try:
            target[0](*target[1])
        except Exception as e:
            if show_errors:
                print(traceback.format_exc())
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(execute_target, target): target for target in targets}

        for future in concurrent.futures.as_completed(futures):
            del futures[future]


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
    def reconstruct_imports():
        global_scope = globals()
        imports = []

        for name, obj in global_scope.items():
            # Check if the object is a module or an alias of a module
            if isinstance(obj, types.ModuleType):
                # Get the original module name from sys.modules
                for mod_name, mod_obj in sys.modules.items():
                    if mod_obj is obj:
                        # Detect if an alias is used
                        if name == mod_name.split(".")[0]:
                            imports.append(f"import {mod_name}")
                        else:
                            imports.append(f"import {mod_name} as {name}")
                        break
        imports.pop(0)
        return "\n".join(imports)
    
    cap_string = b'|'+bytes(zhmiscellany.string.get_universally_unique_string(), 'u8')+b'|'
    
    code = \
'''import dill
import zlib
import sys
import pickle
import traceback
func = dill.loads(zlib.decompress('''+repr(zlib.compress(dill.dumps(func), 9))+'''))
args_list = dill.loads(zlib.decompress('''+repr(zlib.compress(dill.dumps(args), 9))+f'''))
def wrapper_function(*args, **kwargs):
    return func(*args, **kwargs)
if __name__ == "__main__":
    data = [None, None]
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
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
        raise Exception('Critical error when trying to execute temporary file.')
    raw = result.stdout
    # very annoying fix for ansi code at the start and end of the output, also a fix for if the passed functions have their own console output
    try:
        raw = raw.split(cap_string)[1].split(cap_string)[0]
    except:
        raise Exception('Critical error in temporary file.')
    
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