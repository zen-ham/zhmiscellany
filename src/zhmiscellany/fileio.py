from ._fileio_supportfuncs import is_junction
import json, os, shutil, dill, sys, pickle, base64, zlib
import zhmiscellany.string
import zhmiscellany.misc
import hashlib


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


def save_object_to_file(object, file_name):
    with open(file_name, 'wb') as f:
        f.write(fast_dill_dumps(object))


def load_object_from_file(file_name):
    with open(file_name, 'rb') as f:
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
                    pass
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