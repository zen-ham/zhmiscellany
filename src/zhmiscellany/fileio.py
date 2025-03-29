from ._fileio_supportfuncs import is_junction
import json, os, shutil, dill, sys, pickle, base64, zlib
import zhmiscellany.string
import zhmiscellany.misc
import hashlib
from collections import defaultdict
from itertools import chain
import tempfile
import random


def read_json_file(file_path):
    """
    Reads JSON data from a file and returns it as a dictionary.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        with open(file_path, 'w') as f:
            f.write('{}')
        data = {}
    return data


def write_json_file(file_path, data):
    """
    Writes a dictionary to a JSON file.
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def remove_folder(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)


def base_name_no_ext(file_path):
    base_name = os.path.basename(file_path)
    base_name_without_extension, _ = os.path.splitext(base_name)
    return base_name_without_extension


def convert_name_to_filename(name):
    return zhmiscellany.string.multi_replace(name, [("/","["), (":","]"), (".","+")])


def convert_filename_to_name(filename):
    return zhmiscellany.string.multi_replace(filename, [("[","/"), ("]",":"), ("+",".")])


def recursive_copy_files(source_dir, destination_dir, prints=False):
    if prints:
        print('Validating matching directory structure')
    for root, dirs, files in os.walk(source_dir):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            dest_dir_path = os.path.join(destination_dir, os.path.relpath(dir_path, source_dir))

            if not os.path.exists(dest_dir_path):
                print(f'Creating missing directory {dest_dir_path}')
                os.makedirs(dest_dir_path)

    if prints:
        print('Getting a list of files in the source directory')
    source_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            source_files.append(os.path.join(root, file))

    if prints:
        print('Getting a list of files in the destination directory')
    dest_files = []
    for root, _, files in os.walk(destination_dir):
        for file in files:
            dest_files.append(os.path.join(root, file))


    if prints:
        print('Copying files from source to destination, skipping duplicates')
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            source_file = os.path.join(root, file)
            rel_path = os.path.relpath(source_file, source_dir)
            dest_file = os.path.join(destination_dir, rel_path)

            if not os.path.exists(dest_file):
                if prints:
                    print(f'Copying {source_file}')
                shutil.copy2(source_file, dest_file)
            elif os.path.getmtime(source_file) != os.path.getmtime(dest_file):
                if prints:
                    print(f'Copying {source_file}')
                shutil.copy2(source_file, dest_file)


def empty_directory(directory_path):
    # Iterate over all items in the directory
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)

        if os.path.isfile(item_path):
            # If it's a file, delete it
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            # If it's a directory, delete it recursively
            shutil.rmtree(item_path)


def abs_listdir(path):
    return [os.path.join(path, file) for file in os.listdir(path)]


def delete_ends_with(directory, string_endswith, avoid=[]):
    files = abs_listdir(directory)
    for file in files:
        if file.endswith(string_endswith):
            if not file in avoid:
                os.remove(file)


def read_bytes_section(file_path, section_start, section_end):
    with open(file_path, 'rb') as file:
        file.seek(section_start)  # Move the file pointer to the 'start' position
        bytes_to_read = section_end - section_start
        data = file.read(bytes_to_read)  # Read 'bytes_to_read' number of bytes

    return data


def copy_file_with_overwrite(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy2(src, dst)


def fast_dill_dumps(object):
    try:
        data = pickle.dumps(object, protocol=5)  # pickle is much faster so at least attempt to use it at first
    except:
        data = dill.dumps(object, protocol=5)
    return data


def fast_dill_loads(data):
    try:
        object = pickle.loads(data)  # pickle is much faster so at least attempt to use it at first
    except:
        object = dill.loads(data)
    return object


def save_object_to_file(object, file_name, compressed=False):
    with open(file_name, 'wb') as f:
        if compressed:
            f.write(zlib.compress(fast_dill_dumps(object)))
        else:
            f.write(fast_dill_dumps(object))


def load_object_from_file(file_name, compressed=False):
    with open(file_name, 'rb') as f:
        if compressed:
            return fast_dill_loads(zlib.decompress(f.read()))
        else:
            return fast_dill_loads(f.read())


def pickle_and_encode(obj):
    """Pickles an object and URL-safe encodes it."""
    pickled_data = zlib.compress(fast_dill_dumps(obj), 9)  # Serialize the object
    encoded_data = base64.urlsafe_b64encode(pickled_data).decode()  # Base64 encode
    return encoded_data

def decode_and_unpickle(encoded_str):
    """Decodes a URL-safe encoded string and unpickles the object."""
    pickled_data = base64.urlsafe_b64decode(encoded_str)  # Decode from Base64
    obj = fast_dill_loads(zlib.decompress(pickled_data))  # Deserialize
    return obj


def list_files_by_modified_time(directory):
    files_with_times = [(file, os.path.getmtime(os.path.join(directory, file))) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    sorted_files = sorted(files_with_times, key=lambda x: x[1], reverse=True)
    sorted_file_names = [file for file, _ in sorted_files]

    return sorted_file_names


def get_script_path():
    if getattr(sys, 'frozen', False):
        # Running as a standalone executable
        return sys.executable
    else:
        # Running as a Python script
        return sys.argv[0]


def chdir_to_script_dir():
    os.chdir(os.path.dirname(get_script_path()))


def cache(seed, function):
    cache_folder = 'zhmiscellany_cache'
    zhmiscellany.fileio.create_folder(cache_folder)

    def generate_hash(obj):
        obj_str = str(obj)
        return hashlib.md5(obj_str.encode()).hexdigest()

    seed_hash = generate_hash(seed)

    cache_file = f'{cache_folder}/fn_cache_{seed_hash}.pkl'

    if os.path.exists(cache_file):
        return load_object_from_file(cache_file)
    else:
        result = function(seed)
        save_object_to_file(result, cache_file)
        return result


def load_all_cached():
    cache_folder = 'zhmiscellany_cache'
    if os.path.exists(cache_folder):
        files = abs_listdir(cache_folder)
        files = [file for file in files if 'fn_cache_' in file]
        if files:
            return [load_object_from_file(file) for file in files]
        else:
            raise Exception('Nothing has been cached yet')
    else:
        raise Exception('Nothing has been cached yet')


def list_files_recursive(folder):
    files = []
    try:
        for entry in os.scandir(folder):
            if entry.is_file():
                files.append(entry.path)
            elif entry.is_symlink() or is_junction(entry):
                continue
            elif entry.is_dir():
                files.extend(list_files_recursive(entry.path))
    except (PermissionError, FileNotFoundError):
        pass
    return files


def list_files_recursive_multiprocessed(dir_path, return_folders=False):
    def is_junction(entry):
        try:
            st = entry.stat(follow_symlinks=False)
            # On Windows, st_file_attributes is available.
            # FILE_ATTRIBUTE_REPARSE_POINT (0x400) indicates a reparse point (e.g. junction).
            return hasattr(st, "st_file_attributes") and bool(st.st_file_attributes & 0x400)
        except Exception:
            return False
    
    def traversal(dir_path, depth):
        depth += 1
        files = []
        folders = []
        tasks = []
        try:
            for entry in os.scandir(dir_path):
                if entry.is_file():
                    files.append(entry.path)
                elif entry.is_symlink() or is_junction(entry):
                    continue
                elif entry.is_dir():
                    folders.append(entry.path)
                    if depth > max_python_depth:
                        tasks.append((traversal, (entry.path, -99999)))
                    else:
                        new_files, new_folders, new_tasks = traversal(entry.path, depth)
                        files.extend(new_files)
                        folders.extend(new_folders)
                        tasks.extend(new_tasks)
        except (PermissionError, FileNotFoundError):
            pass
        return (files, folders, tasks)
    
    max_python_depth = 1
    files, folders, tasks = traversal(dir_path, 0)
    file_groups = zhmiscellany.processing.batch_multiprocess(tasks)
    for group in file_groups:
        files.extend(group[0])
        folders.extend(group[1])
    if return_folders:
        return files, folders
    else:
        return files


def encode_safe_filename(s, max_length=16):
    """Encodes a string into a short, URL-safe, and file name-safe string."""
    encoded = base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")  # URL-safe encoding
    if len(encoded) > max_length:  # Truncate if too long
        encoded = hashlib.md5(s.encode()).hexdigest()[:max_length]  # Use a hash
    return encoded


def list_files_recursive_cache_optimised_multiprocessed(dir_path, show_timings=False, cache_in_temp=True):
    def is_junction(entry):
        try:
            st = entry.stat(follow_symlinks=False)
            # On Windows, st_file_attributes is available.
            # FILE_ATTRIBUTE_REPARSE_POINT (0x400) indicates a reparse point (e.g. junction).
            return hasattr(st, "st_file_attributes") and bool(st.st_file_attributes & 0x400)
        except Exception:
            return False
    
    def traversal(dir_path, depth=0):
        depth += 1
        files = defaultdict(list)
        folders = []
        tasks = []
        try:
            for entry in os.scandir(dir_path):
                if entry.is_file():
                    files[dir_path].append(entry.path)
                elif entry.is_symlink() or is_junction(entry):
                    continue
                elif entry.is_dir():
                    folders.append(entry.path)
                    if depth > max_python_depth:
                        tasks.append((traversal, (entry.path, -99999)))
                    else:
                        new_files, new_folders, new_tasks = traversal(entry.path, depth)
                        files.update(new_files)
                        folders.extend(new_folders)
                        tasks.extend(new_tasks)
        except (PermissionError, FileNotFoundError):
            pass
        return (files, folders, tasks)
    
    def list_folder(folder):
        files, folders = defaultdict(list), []
        try:
            for entry in os.scandir(folder):
                if entry.is_file():
                    files[folder].append(entry.path)
                elif entry.is_symlink() or is_junction(entry):
                    continue
                elif entry.is_dir():
                    folders.append(entry.path)
        except (PermissionError, FileNotFoundError):
            pass
        return files, folders
    
    def split_into_n_groups(lst, n):
        avg_size = len(lst) // n
        remainder = len(lst) % n
        sublists = []
        
        start = 0
        for i in range(n):
            end = start + avg_size + (1 if i < remainder else 0)  # Distribute remainder
            sublists.append(lst[start:end])
            start = end
        sublists = [sublist for sublist in sublists if sublist]
        return sublists
    
    def get_m_times(folders):
        groups = split_into_n_groups(folders, scan_mtime_worker_count)
        
        def atom(folders):
            mtimes = {}
            for folder in folders:
                try:
                    mtimes[folder] = os.path.getmtime(folder)
                except:
                    pass
            return mtimes
        
        tasks = [(atom, (group,)) for group in groups]
        results = zhmiscellany.processing.batch_multiprocess(tasks)
        mtimes = {}
        for i in results:
            mtimes.update(i)
        return mtimes
    
    # parameters
    scan_mtime_worker_count = 8
    scan_changed_folders_thread_group_count = 64
    fully_update_cache_threshold = 2**10
    cache_compression = False
    # end parameters
    
    if cache_in_temp:
        cache_folder = tempfile.gettempdir()
    else:
        cache_folder = 'zhmiscellany_cache'
        zhmiscellany.fileio.create_folder(cache_folder)
    
    cache_id = encode_safe_filename(dir_path)
    cache_file = f'GFI_{cache_id}.pkl'
    cache_file = os.path.join(cache_folder, cache_file)
    
    if show_timings: zhmiscellany.misc.time_it(None, 'lfrcom')
    if show_timings: zhmiscellany.misc.time_it(None, 'lfrcomt')
    
    max_python_depth = 1
    if not os.path.exists(cache_file):
        files, folders, tasks = traversal(dir_path)
        if show_timings: zhmiscellany.misc.time_it('initial traversal', 'lfrcom')
        
        file_groups = zhmiscellany.processing.batch_multiprocess(tasks)
        if show_timings: zhmiscellany.misc.time_it('multiprocessed deep traversal', 'lfrcom')
        for group in file_groups:
            files.update(group[0])
            folders.extend(group[1])
        if show_timings: zhmiscellany.misc.time_it('extending data', 'lfrcom')
        
        folders = get_m_times(folders)
        zhmiscellany.fileio.save_object_to_file((files, folders), cache_file, compressed=cache_compression)
        if show_timings: zhmiscellany.misc.time_it('creating cache', 'lfrcom')
        return list(chain.from_iterable(files.values()))
    else:
        files, folders = zhmiscellany.fileio.load_object_from_file(cache_file, compressed=cache_compression)
        if show_timings: zhmiscellany.misc.time_it('loading cache', 'lfrcom')
    
    fl_list = list(folders.keys())
    new_folders = get_m_times(fl_list)
    if show_timings: zhmiscellany.misc.time_it(f'getting m times of {len(fl_list)} folders', 'lfrcom')
    changed_folders = []
    for folder, mtime in new_folders.items():
        if folders[folder] != mtime:
            changed_folders.append(folder)
    random.shuffle(changed_folders)
    if show_timings: zhmiscellany.misc.time_it(f'creating {len(changed_folders)} changed folders', 'lfrcom')
    
    for i in changed_folders:  # clear files that might not exist
        try:
            del files[i]
        except KeyError:  # it is possible that the only thing that changed in a folder is another folder, so in that case it would not be inside the file dict
            pass
    
    if show_timings: zhmiscellany.misc.time_it(f'filtering files for changes', 'lfrcom')
    
    def atom(_folders):
        atom_files, atom_folders = defaultdict(list), []
        for _folder in _folders:
            fil, fol = list_folder(_folder)
            atom_files.update(fil)
            for fold in fol:
                if fold not in new_folders:
                    atom_folders.append(fold)
                    fil, fo, _ = traversal(fold, -99999)
                    atom_files.update(fil)
                    atom_folders.extend(fo)
        return atom_files, atom_folders
    
    groups = split_into_n_groups(changed_folders, scan_changed_folders_thread_group_count)
    tasks = [(atom, (group,)) for group in groups]
    
    results = zhmiscellany.processing.batch_threading(tasks)
    if show_timings: zhmiscellany.misc.time_it('multithreading processing changed folders', 'lfrcom')
    
    new_new_folders = []
    for fi, fo in results:
        files.update(fi)
        new_new_folders.extend(fo)
    
    if len(changed_folders) > fully_update_cache_threshold:
        new_folders.update(get_m_times(new_new_folders))
        if show_timings: zhmiscellany.misc.time_it(f'get m times of {len(new_new_folders)} new folders')
        
        zhmiscellany.fileio.save_object_to_file((files, new_folders), cache_file)
        
        if show_timings: zhmiscellany.misc.time_it(f'writing to cache')
    
    ret = list(chain.from_iterable(files.values()))
    
    if show_timings: zhmiscellany.misc.time_it('Everything together', 'lfrcomt')
    
    return ret