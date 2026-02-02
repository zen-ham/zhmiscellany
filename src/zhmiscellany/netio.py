import os, requests
import zhmiscellany.string
import sys

WIN32_AVAILABLE = False
if sys.platform == "win32":
    try:
        from zhmiscellany._misc_supportfuncs import patch_rhg
        from random_header_generator import HeaderGenerator
        WIN32_AVAILABLE = True
    except ImportError:
        print("Warning: random_header_generator not available, Windows-specific features disabled")


def resolve_file(url, destination_folder="."):
    import urllib.parse
    file_name = urllib.parse.unquote(url.split("/")[-1])
    file_name = file_name.split('?')[0]
    destination_path = f"{destination_folder}/{file_name}"
    if len(destination_path) > 250:
        destination_path = f'{destination_path[:(250 - len(os.path.splitext(destination_path)[1]))]}{os.path.splitext(destination_path)[1]}'
    return destination_path


def download_file(url, destination_folder=".", just_return_path=False, headers=None, file_path=None):
    from urllib3.exceptions import InsecureRequestWarning
    import urllib3
    urllib3.disable_warnings(InsecureRequestWarning)

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
            for chunk in response.iter_content(chunk_size=2**12):
                file.write(chunk)

        return destination_path

    else:
        raise Exception(f"Failed to download the file. Status code: {response.status_code}")


def generate_headers(url):
    import urllib.parse
    headers = {}
    
    if WIN32_AVAILABLE:
        generator = HeaderGenerator()
        for k, v in generator().items():
            headers[k] = v

    headers['Referer'] = url
    headers['Host'] = urllib.parse.urlparse(url).netloc

    return headers


def is_internet():
    urls = [
        "http://1.1.1.1",
        "https://www.google.com",
        "https://yandex.com/",
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=5, verify=False)
            if 200 <= res.status_code < 300:
                return True
        except:
            pass
    return False
