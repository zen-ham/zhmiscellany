
import requests
import xml.etree.ElementTree as ET

# PasteBin API Class - Developed by acidvegas in Python, modernized for use in zhmiscellany package. (https://git.acid.vegas/pastebin)
class PasteBin:
    def __init__(self, api_dev_key, api_user_key=None):
        self.api_dev_key = api_dev_key
        self.api_user_key = api_user_key

    def api_call(self, method, params):
        '''Make a call to the PasteBin API.'''
        url = f'https://pastebin.com/api/{method}'
        response = requests.post(url, data=params, timeout=10)
        try:
            response.raise_for_status()  # Raise an exception for HTTP errors
        except:
            raise Exception(f'ERROR {response.status_code}: {response.text}')
        return response.text

    def create_user_key(self, username, password):
        '''Create a user key for the PasteBin API.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_user_name': username,
            'api_user_password': password
        }
        return self.api_call('api_login.php', params)

    def paste(self, data, guest=False, name=None, format=None, private=None, expire=None):
        '''Create a paste on PasteBin.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_option': 'paste',
            'api_paste_code': data
        }
        if not guest:
            params['api_user_key'] = self.api_user_key
        if name:
            params['api_paste_name'] = name
        if format:
            params['api_paste_format'] = format
        if private:
            params['api_paste_private'] = private
        if expire:
            params['api_paste_expire_date'] = expire
        return self.api_call('api_post.php', params)

    def list_pastes(self, results_limit=None):
        '''List pastes created by the user.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_user_key': self.api_user_key,
            'api_option': 'list'
        }
        if results_limit:
            params['api_results_limit'] = results_limit
        root = ET.fromstring(f"<root>{self.api_call('api_post.php', params)}</root>")
        pastes_list = []
        for paste in root.findall('paste'):
            paste_dict = {child.tag: child.text for child in paste}
            pastes_list.append(paste_dict)
        return pastes_list

    def trending_pastes(self):
        '''List trending pastes.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_option': 'trends'
        }
        return self.api_call('api_post.php', params)

    def delete_paste(self, paste_key):
        '''Delete a paste.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_user_key': self.api_user_key,
            'api_paste_key': paste_key,
            'api_option': 'delete'
        }
        return self.api_call('api_post.php', params)

    def user_info(self):
        '''Get information about the user.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_user_key': self.api_user_key,
            'api_option': 'userdetails'
        }
        return self.api_call('api_post.php', params)

    def raw_pastes(self, paste_key):
        '''Get the raw data of a paste.'''
        params = {
            'api_dev_key': self.api_dev_key,
            'api_user_key': self.api_user_key,
            'api_paste_key': paste_key,
            'api_option': 'show_paste'
        }
        return self.api_call('api_raw.php', params)


class Pasteee:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.paste.ee/v1/pastes"

    def api_call(self, method, endpoint, params=None, json_data=None):
        '''Make a call to the Pastee API.'''
        headers = {'X-Auth-Token': self.api_key}
        url = f"{self.base_url}{endpoint}"

        if method == 'POST':
            response = requests.post(url, headers=headers, json=json_data, params=params, timeout=10)
        elif method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=10)

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f'ERROR {response.status_code}: {response.text}') from e

        return response.json()

    def paste(self, data, name=None, description=None, expire=None, syntax=None):
        '''Create a paste on Pastee.'''
        json_data = {
            'sections': [{'contents': data}]
        }
        if expire:
            json_data['expiration'] = expire
        if description:
            json_data['description'] = description
        if name:
            json_data['sections'][0]['name'] = name
        if syntax:
            json_data['sections'][0]['syntax'] = syntax

        return self.api_call('POST', '', json_data=json_data)

    def get_paste(self, paste_id):
        '''Retrieve a paste by its ID.'''
        return self.api_call('GET', f'/{paste_id}')

    def delete_paste(self, paste_id):
        '''Delete a paste by its ID.'''
        return self.api_call('DELETE', f'/{paste_id}')

    def list_pastes(self, per_page=None, page=None):
        '''List all pastes on account.'''
        perameters = {}
        if page:
            perameters['page'] = page
        if per_page:
            perameters['perpage'] = per_page
        return self.api_call('GET', '')
