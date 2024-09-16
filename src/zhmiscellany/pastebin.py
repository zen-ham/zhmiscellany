# PasteBin API Class - Developed by acidvegas in Python, modernized for use in zhmiscellany package. (https://git.acid.vegas/pastebin)

'''
API Documentation: https://pastebin.com/doc_api
'''

import requests
import xml.etree.ElementTree as ET


class PasteBin:
    def __init__(self, api_dev_key, api_user_key=None):
        self.api_dev_key = api_dev_key
        self.api_user_key = api_user_key

    def api_call(self, method, params):
        '''Make a call to the PasteBin API.'''
        url = f'https://pastebin.com/api/{method}'
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
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
