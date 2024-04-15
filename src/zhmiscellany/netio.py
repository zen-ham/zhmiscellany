import os, requests
import zhmiscellany.string
import urllib.parse
from random_header_generator import HeaderGenerator


def resolve_file(url, destination_folder="."):
    file_name = urllib.parse.unquote(url.split("/")[-1])
    file_name = file_name.split('?')[0]
    destination_path = f"{destination_folder}/{file_name}"
    if len(destination_path) > 250:
        destination_path = f'{destination_path[:(250 - len(os.path.splitext(destination_path)[1]))]}{os.path.splitext(destination_path)[1]}'
    return destination_path


def download_file(url, destination_folder=".", just_return_path=False, headers=None, file_path=None):
    if file_path:
        destination_path = file_path
    else:
        destination_path = resolve_file(url, destination_folder)

    if os.path.exists(destination_path):
        if just_return_path:
            return destination_path
        return False
    if headers:
        response = requests.get(url, stream=True, headers=headers)
    else:
        response = requests.get(url, stream=True)
    if response.status_code == 200:

        # Save the file
        with open(destination_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)

        return destination_path

    else:
        raise Exception(f"Failed to download the file. Status code: {response.status_code}")


def generate_headers(url):
    generator = HeaderGenerator()
    headers = {
    }

    for k, v in generator().items():
        headers[k] = v

    headers['Referer'] = url
    headers['Host'] = urllib.parse.urlparse(url).netloc

    return headers