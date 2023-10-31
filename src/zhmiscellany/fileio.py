import json, os, shutil
import zhmiscellany.string


def read_json_file(file_path):
    """
    Reads JSON data from a file and returns it as a dictionary.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        with open(file_path, 'w') as f:
            f.write('')
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
            #print(f'Deleting {item_path}')
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            # If it's a directory, delete it recursively
            #print(f'Removing {item_path}')
            shutil.rmtree(item_path)


def abs_listdir(path):
    return [os.path.join(path, file) for file in os.listdir(path)]


def delete_ends_with(directory, string_endswith, avoid=[]):
    files = abs_listdir(directory)
    for file in files:
        if file.endswith(string_endswith):
            if not file in avoid:
                os.remove(file)