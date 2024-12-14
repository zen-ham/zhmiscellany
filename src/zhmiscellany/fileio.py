import json, os, shutil, dill, sys
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


def save_object_to_file(object, file_name):
    with open(file_name, 'wb') as f:
        dill.dump(object, f, protocol=5)


def load_object_from_file(file_name):
    with open(file_name, 'rb') as f:
        return dill.load(f)


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


def cache(seed, function):
    def generate_hash(obj):
        obj_str = str(obj)
        return hashlib.md5(obj_str.encode()).hexdigest()

    seed_hash = generate_hash(seed)

    cache_file = f'{seed_hash}.pkl'

    if os.path.exists(cache_file):
        return load_object_from_file(cache_file)
    else:
        result = function(seed)
        save_object_to_file(result, cache_file)
        return result
