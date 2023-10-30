import sys
import time
import re
import discum
import zhmiscellany.fileio
import zhmiscellany.string
import os
import threading
from PIL import Image
import pytesseract
import pkg_resources


def calculateOption(guild_id, action):  # action == 'append' or 'replace'
    if action == 'append':
        lastUserIDs = _bot.gateway.guildMemberSearches[guild_id]["queries"][''.join(_Queries.qList)]
        data = [_bot.gateway.session.guild(guild_id).members[i] for i in _bot.gateway.session.guild(guild_id).members if i in lastUserIDs]
        lastName = sorted(set([re.sub(' +', ' ', j['nick'].lower()) if (j.get('nick') and re.sub(' +', ' ', j.get('nick').lower()).startswith(''.join(_Queries.qList))) else re.sub(' +', ' ', j['username'].lower()) for j in data]))[-1]
        try:
            option = lastName[len(_Queries.qList)]
            return option
        except IndexError:
            return None
    elif action == 'replace':
        if _Queries.qList[-1] in _allchars:
            options = _allchars[_allchars.index(_Queries.qList[-1]) + 1:]
            if ' ' in options and (len(_Queries.qList) == 1 or (len(_Queries.qList) > 1 and _Queries.qList[-2] == ' ')):  # cannot start with a space and cannot have duplicate spaces
                options.remove(' ')
            return options
        else:
            return None


def findReplaceableIndex(guild_id):
    for i in range(len(_Queries.qList) - 2, -1, -1):  # assume that the last index is not changable
        if _Queries.qList[i] != '~':
            return i
    return None


def bruteForceTest(resp, guild_id, wait):
    if resp.event.guild_members_chunk:
        remove = False
        if len(_bot.gateway.guildMemberSearches[guild_id]["queries"][''.join(_Queries.qList)]) == 100:  # append
            appendOption = calculateOption(guild_id, 'append')
            if appendOption:
                _Queries.qList.append(appendOption)
            else:
                remove = True
        else:  # if <100 results returned, replace
            replaceOptions = calculateOption(guild_id, 'replace')
            if replaceOptions:
                _Queries.qList[-1] = replaceOptions[0]
            else:
                remove = True
        if remove:  # if no replace options, find first replaceable index & replace it
            if len(_Queries.qList) == 1:  # reached end of possibilities
                _bot.gateway.removeCommand(bruteForceTest)
                _bot.gateway.close()
            else:
                replaceableInd = findReplaceableIndex(guild_id)
                if replaceableInd != None:
                    _Queries.qList = _Queries.qList[:replaceableInd + 1]
                    replaceOptions = calculateOption(guild_id, 'replace')
                    _Queries.qList[-1] = replaceOptions[0]
                else:
                    _bot.gateway.removeCommand(bruteForceTest)
                    _bot.gateway.close()
        if wait: time.sleep(wait)
        print_str_if("members fetched so far: {}".format(len(_bot.gateway.session.guild(guild_id).members)), _scrape_guild_use_console)
        _bot.gateway.queryGuildMembers([guild_id], query=''.join(_Queries.qList), limit=100, keep="all")


def after_op14_fetching(resp, guild_id, use_op8=True, wait=1):
    if _bot.gateway.finishedMemberFetching(guild_id):
        _bot.gateway.removeCommand({'function': after_op14_fetching, 'params': {'guild_id': guild_id, 'use_op8': use_op8, 'wait': wait}})
        num_members = len(_bot.gateway.session.guild(guild_id).members)
        print_str_if('Finished op14 member fetching. Fetched {} members from guild {}'.format(num_members, guild_id), _scrape_guild_use_console)
        if use_op8 and _bot.gateway.session.guild(guild_id).memberCount > num_members:
            print_str_if('scraping members using op8 (this might take a while)...', _scrape_guild_use_console)
            _bot.gateway.command({"function": bruteForceTest, "params": {"guild_id": guild_id, "wait": wait}})
            _bot.gateway.queryGuildMembers([guild_id], query=''.join(_Queries.qList), limit=100, keep="all")  # have to put this down here since the gateway is already running
        else:
            _bot.gateway.close()


def get_members(guild_id, channel_id, extra_scrape=True, wait=1):  # combination of op14 and op8 member fetching
    print_str_if('scraping members using op14...', _scrape_guild_use_console)
    _bot.gateway.fetchMembers(guild_id, channel_id, keep="all", reset=False, wait=wait)
    _bot.gateway.command({'function': after_op14_fetching, 'params': {'guild_id': guild_id, 'use_op8': extra_scrape, 'wait': wait}})
    _bot.gateway.run()
    return _bot.gateway.session.guild(guild_id).members


def scrape_guild_internal(guild_id, channel_id, user_token, console=False):
    global _bot, _allchars, _Queries, _scrape_guild_use_console
    _scrape_guild_use_console = console
    _bot = discum.Client(token=user_token, log=False)

    _bot.gateway.resetMembersOnSessionReconnect = False  # member fetching might take a while

    # code for op8 fetching
    _allchars = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~']
    _bot.gateway.guildMemberSearches = {}

    class _Queries:
        qList = ["!"]  # query list

    members = get_members(guild_id, channel_id, extra_scrape=True, wait=1)
    return members  # returns a dict where the keys are user id strings


def scrape_guild(guild_id, channel_id, user_token, use_cache=True, console=False):
    if use_cache:
        cache_folder = 'zhmiscellany_cache'
        potential_path = os.path.join(cache_folder, f'{guild_id}_members.json')
        if os.path.exists(potential_path):
            return zhmiscellany.fileio.read_json_file(potential_path)

        data = scrape_guild_internal(guild_id, channel_id, user_token, console)
        zhmiscellany.fileio.create_folder(cache_folder)
        zhmiscellany.fileio.write_json_file(potential_path, data)
        return data

    return scrape_guild_internal(guild_id, channel_id, user_token, console)


def count_threads_by_string(string):
    count = 0
    for thread in threading.enumerate():
        if isinstance(thread, threading.Thread) and string in thread.name:
            count += 1
    return count


def print_str_if(string, print_it):
    if print_it:
        sys.stdout.write(string+'\n')


def set_tesseract_path():
    tesseract_path = pkg_resources.resource_filename(__name__, 'resources/tesseract')
    pytesseract.pytesseract.tesseract_cmd = f'{tesseract_path}\\tesseract.exe'


def ocr(image_path):
    set_tesseract_path()
    try:
        if '.ico' in image_path:
            ico_file = Image.open(image_path)
            png_file = ico_file.convert("RGBA")
            text = pytesseract.image_to_string(png_file)
        else:
            text = pytesseract.image_to_string(Image.open(image_path))
        print_str_if(f'succeeded {image_path}', _batch_ocr_use_console)
        return text
    except Exception as e:
        print_str_if(f'\nfailed {image_path}\n\n{e}\n', _batch_ocr_use_console)
        return ''


def l_ocr(image_path, thread_string):
    _batch_ocr_cache_dict[thread_string][image_path] = ocr(image_path)


_batch_ocr_cache_dict = {}


def batch_ocr(image_paths, threads=10, prints=False):
    set_tesseract_path()
    global _batch_ocr_use_console, _batch_ocr_cache_dict, thread_string
    _batch_ocr_use_console = prints
    thread_string = zhmiscellany.string.get_universally_unique_string()
    _batch_ocr_cache_dict[thread_string] = {}
    l_image_paths = image_paths[:]
    while len(l_image_paths) > 0:
        while count_threads_by_string(thread_string) < threads:
            path = l_image_paths.pop()
            threading.Thread(target=l_ocr, args=(path, thread_string), name=f'{thread_string}_{zhmiscellany.string.get_universally_unique_string()}').start()
            if len(l_image_paths) < 1:
                break
        time.sleep(0.1)

    while count_threads_by_string(thread_string) or thread_string not in _batch_ocr_cache_dict:
        time.sleep(0.1)

    output_dict = {}
    for each in _batch_ocr_cache_dict[thread_string]:
        output_dict[each] = _batch_ocr_cache_dict[thread_string][each]
    _batch_ocr_cache_dict.pop(thread_string)

    return output_dict
