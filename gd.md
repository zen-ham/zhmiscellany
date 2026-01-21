`zhmiscellany`,
=

An organized collection of unique and useful functions/classes/modules/bindings.
-

[Introduction](https://github.com/zen-ham/zhmiscellany/tree/master#Introduction)\
[Documentation](https://github.com/zen-ham/zhmiscellany/tree/master#Documentation)\
[![PyPI Downloads](https://static.pepy.tech/badge/zhmiscellany)](https://pepy.tech/projects/zhmiscellany) [![PyPI Downloads](https://static.pepy.tech/badge/zhmiscellany/month)](https://pepy.tech/projects/zhmiscellany) ![lastcommitbadge](https://img.shields.io/github/last-commit/zen-ham/zhmiscellany)

---

Introduction
===

Can be installed with `pip install zhmiscellany`

Supports Linux! (Some functionality reduced)

Currently, the package stands at <func_token> functions/classes/bindings across <module_token> modules.

The git repository for this package can be found [here](https://github.com/zen-ham/zhmiscellany). The docs also look nicer on github.

If you wish to reach out, you may add @z_h_ on Discord, or join [the server](https://discord.gg/ThBBAuueVJ).

Believe it or not this package is not a monolith, I've split off some functionality into a handful of other packages to keep zhmiscellany from becoming too bloated: [zhmiscellanygsudo](https://pypi.org/project/zhmiscellanygsudo/), [zhmiscellanyocr](https://pypi.org/project/zhmiscellanyocr/), [zhmiscellanyrusteffect](https://pypi.org/project/zhmiscellanyrusteffect/).

---

Documentation:
===

[Usage-examples](https://github.com/zen-ham/zhmiscellany/blob/master/README.md#usage-examples) Usage examples for the discord module.\
[zhmiscellany.discord](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanydiscord) Functions for interacting with discord in various ways.\
[zhmiscellany.rust](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyrust) Various rust bindings aimed towards speed.\
[zhmiscellany.cpp](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanycpp) Various C++ bindings aimed towards speed.\
[zhmiscellany.macro](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanymacro) Functions with very high flexibility and speed for simulating interactions with mouse and keyboard.\
[zhmiscellany.fileio](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyfileio) Functions for interacting with local files, such as pickle, json and other file related functions I find useful.\
[zhmiscellany.string](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanystring) Functions for interacting with/generating strings that I find useful.\
[zhmiscellany.math](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanymath) Functions for making some calculations easier.\
[zhmiscellany.netio](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanynetio) Internet related functions that didn't make sense in any other module.\
[zhmiscellany.image](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyimage) Functions for quantifying and manipulating images.\
[zhmiscellany.list](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanylist) Functions for manipulating lists.\
[zhmiscellany.dict](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanydict) Functions for working with dicts.\
[zhmiscellany.processing](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyprocessing) Functions for processing/multiprocessing using flexible high level ray wrappers, homebrew high level multiprocessing implementations, or in threads in a more straight forward way.\
[zhmiscellany.misc](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanymisc) Miscellaneous functions that didn't fit anywhere else. There's alot of useful stuff here.\
[zhmiscellany.pipes](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanypipes) Classes and functions for effectively using pipes for IPC (Inter-Process Communication)\
[zhmiscellany.gui](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanygui) GUI related utilities for quickly adding visual components where it's needed.


Usage examples
===
A script that caches and prints out the user IDs of all the members in a server.
```py
import zhmiscellany

members = zhmiscellany.discord.scrape_guild(user_token=zhmiscellany.discord.get_local_discord_user()[0], guild_id='1162030646424768562', channel_id='1162031219471556629')

for member_id in members:
    print(member_id)
```
#
A script that downloads all messages from a server and caches them (aka stores data in json files), Then downloads all the found media files, with print-outs of ETA, % complete, etc.
```py
import zhmiscellany, time, os, re

guild_channels = zhmiscellany.discord.get_guild_channels(zhmiscellany.discord.get_local_discord_user()[0], '1001978777892552884')

channels_message_data = []
for channel in guild_channels:
    channels_message_data.append(zhmiscellany.discord.get_channel_messages(zhmiscellany.discord.get_local_discord_user()[0], channel['id']))

media_dir = r'/scraped_media'

urls = []

count = 0
for messages in channels_message_data:
    for message in messages:
        for attachment in message['attachments']:
            if any(c in attachment['url'].lower() for c in ['.mp4', '.jpg', '.png', '.webp', '.mp3']):
                count += 1
                url = attachment['url'].split('?')[0]
                urls.append(url)

total = count
eta_count = count

timestamps = []
count = 0
for url in urls:
    count += 1
    print(url)
    print(f'{count}, {zhmiscellany.math.smart_percentage(count, total)}%, ETA {zhmiscellany.math.calculate_eta(timestamps, eta_count)}')
    downloaded = (zhmiscellany.netio.download_file(url, f'{media_dir}\\{zhmiscellany.fileio.convert_name_to_filename(url)}', os.path.splitext(url)[1].lower()))
    if downloaded:
        timestamps.append(time.time())
    else:
        eta_count -= 1
```
#
A script that reposts messages you've sent in one channel to many other channels.
```py
import zhmiscellany, time

from_channel = '1122614930617683975'

post_channels = ['880703742096326677', '1141178363885670505']

amount_of_messages = 3

messages = zhmiscellany.discord.get_channel_messages(user_token=zhmiscellany.discord.get_local_discord_user()[0], channel_id=from_channel, limit=amount_of_messages, use_cache=False)
messages.reverse()
for channel in post_channels:
    for message in messages:
        if message['author']['id'] == zhmiscellany.discord.get_local_discord_user()[2]:
            content = message['content']
            attachments = []
            for i in message['attachments']:
                attachments.append(i['url'])
            if len(attachments) > 0:
                if len(content) > 0:
                    content = f'{content} {" ".join(attachments)}'
                else:
                    content = " ".join(attachments)
            zhmiscellany.discord.send_message(zhmiscellany.discord.get_local_discord_user()[0], content, channel)
            print(content)
            time.sleep(1)
```
#
A script that reacts to a bunch of messages in multiple channels, with print-outs of ETA, % complete, etc.
```py
import zhmiscellany, time


channel_ids = ['926310071435145256', '880703742096326677']
channels_message_data = []
amount_of_messages = 100
emojis = ['🇦🇺']

for ide in channel_ids:
    channels_message_data.append(zhmiscellany.discord.get_channel_messages(user_token=zhmiscellany.discord.get_local_discord_user()[0], channel_id=ide, limit=amount_of_messages, use_cache=False))

ids = []

count = 0
for messages in channels_message_data:
    for message in messages:
        count += 1
        ide = [message['id'], message['channel_id']]
        ids.append(ide)

total = count
eta_count = count

timestamps = []
count = 0
for ide in ids:
    count += 1
    print(f'{count}, {zhmiscellany.math.smart_percentage(count, eta_count)}%, ETA {zhmiscellany.math.calculate_eta(timestamps, eta_count)}')
    zhmiscellany.discord.add_reactions_to_message(zhmiscellany.discord.get_local_discord_user()[0], emojis, ide[1], ide[0])
    timestamps.append(time.time())
```
#
A script that prints out the URLs to all the attachments on a message.
```py
import zhmiscellany

message_url = 'https://discord.com/channels/1001978777892552884/1064070189324435466/1162434625092718623'

message = zhmiscellany.discord.get_message(zhmiscellany.discord.get_local_discord_user()[0], zhmiscellany.discord.message_url_to_ids(message_url)[1], zhmiscellany.discord.message_url_to_ids(message_url)[2])

for attachment in message['attachments']:
    url = attachment['url']
    print(url)
```
---

`zhmiscellany.discord`
---

`zhmiscellany.discord.add_reactions_to_message()`
---

`zhmiscellany.discord.add_reactions_to_message(user_token, message_url, emojis)`

Reacts to a message with the given emoji(s).

example:
```py
import zhmiscellany

zhmiscellany.discord.add_reactions_to_message(
    user_token=zhmiscellany.discord.get_local_discord_user()[0],
    emojis=['🦛', '🇦🇺'], 
    channel_id='263894734190280704',
    message_id='263894769158062082'
    )
```

#

`zhmiscellany.discord.get_channel_messages()`
---

`get_channel_messages(user_token, channel_id, limit = 0, use_cache = True)`

Gets any amount of messages from a channel.\
Can also cache the data locally, so that it won't have to re download them when ran for a second time.

example:
```py
import zhmiscellany

last_1000_messages = zhmiscellany.discord.get_channel_messages(
    user_token=zhmiscellany.discord.get_local_discord_user()[0],
    channel_id='263894734190280704',
    limit=1000,
    use_cache=False
    )
```

#

`zhmiscellany.discord.get_local_discord_user()`
---

`zhmiscellany.discord.get_local_discord_user()`

Gets info about the local user, allows code to be run without needing to find your user token every time.\
So if the user is logged into discord on the app or in the browser (on windows) this function can return the data, which can really streamline things.

example:
```py
import zhmiscellany

user_data = zhmiscellany.discord.get_local_discord_user()
user_token = user_data[0]
```

#

`zhmiscellany.discord.get_guild_channels()`
---

`zhmiscellany.discord.get_guild_channels(user_token, guild_id, use_cache=True)`

Gets a dict of all the channels in a server. This one can also cache the data locally, so that it runs instantly the second time around.

example:
```py
import zhmiscellany

guild_channels = zhmiscellany.discord.get_guild_channels(
    user_token=zhmiscellany.discord.get_local_discord_user()[0],
    guild_id='880697939016695850',
    use_cache=True
    )

channel_ids = [channel['id'] for channel in guild_channels]
```

#

`zhmiscellany.discord.send_message()`
---

`zhmiscellany.discord.send_message(user_token, text, channel_id)`

Sends a message in a channel.

example:
```py
import zhmiscellany

zhmiscellany.discord.send_message(
    user_token=zhmiscellany.discord.get_local_discord_user()[0],
    text='Hello, every nyan!',
    channel_id='263894734190280704')
```

#

`zhmiscellany.discord.get_message()`
---

`zhmiscellany.discord.get_message(user_token, channel_id, message_id)`

Gets a message from a channel.

example:
```py
import zhmiscellany

message = zhmiscellany.discord.get_message(
    user_token=zhmiscellany.discord.get_local_discord_user()[0],
    channel_id='263894734190280704',
    message_id='263894769158062082'
    )

content = message['content']
```

#

`zhmiscellany.discord.ids_to_message_url()`
---

`zhmiscellany.discord.ids_to_message_url(channel_id, message_id, guild_id = None)`

Turns ids into a message url. Direct messages don't have a guild id, so the guild_id argument is optional depending on if the message is in a guild channel or a DM channel.

example:
```py
import zhmiscellany

messagw_url = zhmiscellany.discord.ids_to_message_url(
    guild_id='880697939016695850',
    channel_id='880703742096326677',
    message_id='880726566118768640'
    )
```

#

`zhmiscellany.discord.message_url_to_ids()`
---

`zhmiscellany.discord.message_url_to_ids(message_url)`

Turns a message URL into its respective IDs.

example:
```py
import zhmiscellany

message_ids = zhmiscellany.discord.message_url_to_ids(
    'https://discord.com/channels/880697939016695850/880703742096326677/880726566118768640'
    )
guild_id = message_ids[0]
channel_id = message_ids[1]
message_id = message_ids[2]
```

#

`zhmiscellany.discord.scrape_guild()`
---

`scrape_guild(guild_id, channel_id, user_token, use_cache=True, console=False)`

Turns a message URL into its respective IDs.

example:
```py
import zhmiscellany

members = zhmiscellany.discord.scrape_guild(
    user_token=zhmiscellany.discord.get_local_discord_user()[0],
    guild_id='1162030646424768562',
    channel_id='1162031219471556629'
    )

for member_id in members:
    print(member_id)
```

`zhmiscellany.discord.send_type()`
---

`send_type(user_token, channel_id)`

Sends an API request to make it seem like the user is typing in the channel, for 10 seconds.

#

`zhmiscellany.discord.decode_user_id()`
---

`decode_user_id(user_token)`

Decodes any token to user id.

#

`zhmiscellany.discord.get_guilds()`
---

`get_guilds(user_token, use_cache=True)`

Gets info of all guilds the user is in.

#

`zhmiscellany.discord.get_dm_channels()`
---

`get_dm_channels(user_token, use_cache=True)`

Gets info on all DM channels the user has.

#

`zhmiscellany.discord.get_invite_info()`
---

`get_invite_info(user_token, invite_code, use_cache=True)`

Gets info on any invite code.

#

`zhmiscellany.discord.generate_server_invite()`
---

`generate_server_invite(user_token, channel_id)`

Generates a valid invite to any server the user is in.

#

`zhmiscellany.discord.get_approximate_member_count()`
---

`get_approximate_member_count(user_token, channel_id, use_cache=True)`

Gets an approximate member count for any server the user is in. For small servers the count is fully accurate, only for very large servers is it possibly inaccurate.

#

`zhmiscellany.discord.id_to_timestamp()`
---

`id_to_timestamp(id)`

Converts a discord id to a unix timestamp.

#

`zhmiscellany.discord.timestamp_to_id()`
---

`timestamp_to_id(timestamp)`

Converts a unix timestamp to a discord id.

#

`zhmiscellany.discord.get_user_avatar_url()`
---

`get_user_avatar_url(user_token, user_id, use_cache=True)`

Gets a URL to the image someone is using as their avatar.

#<|<discord>|>

`zhmiscellany.dict`
---

`zhmiscellany.dict.print_dict()`
---

`zhmiscellany.dict.print_dict(ldict)`

Prints out a dict in a readable way.

#<|<dict>|>

---
`zhmiscellany.fileio`
---

`zhmiscellany.fileio.read_json_file()`
---

`zhmiscellany.fileio.read_json_file(file_path)`

Reads json data from a json file and returns it as a dict.

#

`zhmiscellany.fileio.write_json_file()`
---

`zhmiscellany.fileio.write_json_file(file_path, data)`

Writes a dict to a json file.

#

`zhmiscellany.fileio.create_folder()`
---

`zhmiscellany.fileio.create_folder(folder_name)`

Creates a folder.

#

`zhmiscellany.fileio.remove_folder()`
---

`zhmiscellany.fileio.remove_folder(folder_name)`

Removes a folder and all contents.

#

`zhmiscellany.fileio.base_name_no_ext()`
---

`zhmiscellany.fileio.base_name_no_ext(file_path)`

Get the name of a file without the ext.

#

`zhmiscellany.fileio.convert_name_to_filename()`
---

`zhmiscellany.fileio.convert_name_to_filename(name)`

Convert a URL like name to a file system like name.

#

`zhmiscellany.fileio.convert_filename_to_name()`
---

`zhmiscellany.fileio.convert_filename_to_name(filename)`

Convert a file system like name back to a URL like name.

#

`zhmiscellany.fileio.recursive_copy_files()`
---

`zhmiscellany.fileio.recursive_copy_files(source_dir, destination_dir, prints=False)`

Copy all the files from a source directory and into a destination directory.

#

`zhmiscellany.fileio.empty_directory()`
---

`zhmiscellany.fileio.empty_directory(directory_path)`

Delete all the files in a directory but not the directory itself.

#

`zhmiscellany.fileio.abs_listdir()`
---

`zhmiscellany.fileio.abs_listdir(path)`

List the files in a directory, returns absolute paths.

#

`zhmiscellany.fileio.delete_ends_with()`
---

`zhmiscellany.fileio.delete_ends_with(directory, string_endswith, avoid=[])`

Delete all the files in a directory that end with a string, optional list of what files to avoid.

#

`zhmiscellany.fileio.read_bytes_section()`
---

`zhmiscellany.fileio.read_bytes_section(file_path, section_start, section_end)`

Read a section of a file without reading the whole thing.

#

`zhmiscellany.fileio.copy_file_with_overwrite()`
---

`zhmiscellany.fileio.copy_file_with_overwrite(src, dst)`

Copies and overwrites a file.

#

`zhmiscellany.fileio.fast_dill_dumps()`
---

`zhmiscellany.fileio.fast_dill_dumps(object)`

Pickle is alot faster than dill, so this function automatically determines which to use, if pickle is available it will use that for speed, else it will simply fall back to dill.

#

`zhmiscellany.fileio.fast_dill_loads()`
---

`zhmiscellany.fileio.fast_dill_loads(data)`

Same idea as fast_dill_dumps but it loads instead of dumps.

#

`zhmiscellany.fileio.save_object_to_file()`
---

`zhmiscellany.fileio.save_object_to_file(object, file_name, compressed=False)`

Saves an object to a file, uses fast_dill_dumps.

#

`zhmiscellany.fileio.load_object_from_file()`
---

`zhmiscellany.fileio.load_object_from_file(file_name, compressed=False)`

Designed to be used along with save_object_to_file but loads instead of saves.

#

`zhmiscellany.fileio.pickle_and_encode()`
---

`zhmiscellany.fileio.pickle_and_encode(obj)`

Pickles an object with fast_dill_dumps, compresses it and encodes it to a URL-safe string.

#

`zhmiscellany.fileio.decode_and_unpickle()`
---

`zhmiscellany.fileio.decode_and_unpickle(encoded_str)`

Designed to be used with pickle_and_encode, simply does the opposite thing and returns an object.

#

`zhmiscellany.fileio.list_files_by_modified_time()`
---

`zhmiscellany.fileio.list_files_by_modified_time(directory)`

Lists the files in a directory ordered by modified time.

#

`zhmiscellany.fileio.get_script_path()`
---

`zhmiscellany.fileio.get_script_path()`

Gets the path to the current file, it also supports PyInstaller EXEs, in which case it will return the path to the EXE.

#

`zhmiscellany.fileio.chdir_to_script_dir()`
---

`zhmiscellany.fileio.chdir_to_script_dir()`

Changes the current working directory to whatever folder the script is in.

#

`zhmiscellany.fileio.cache()`
---

`zhmiscellany.fileio.cache(seed, function)`

Caches the result of a function based on a seed value. Stores and retrieves the cached result from a file.

#

`zhmiscellany.fileio.load_all_cached()`
---

`zhmiscellany.fileio.load_all_cached()`

Loads all cached function results from the cache directory. Raises an exception if nothing is cached.

#

`zhmiscellany.fileio.list_files_recursive()`
---

`zhmiscellany.fileio.list_files_recursive(folder)`

Recursively lists all files in a folder while skipping symlinks and junctions.

#

`zhmiscellany.fileio.list_files_recursive_multiprocessed()`
---

`zhmiscellany.fileio.list_files_recursive_multiprocessed(dir_path, return_folders=False)`

Recursively lists all files in a folder using multiprocessing for efficiency. Optionally returns folder names as well.

#

`zhmiscellany.fileio.list_files_recursive_cache_optimised_multiprocessed()`
---

`zhmiscellany.fileio.list_files_recursive_cache_optimised_multiprocessed(dir_path, show_timings=False, cache_in_temp=True)`

Efficiently lists files recursively using a cache to improve performance. Uses multiprocessing and caching to minimize redundant filesystem access and maximise speed. In testing, it listed the C drive with 1M+ files in 2.0s.

#<|<fileio>|>

---
`zhmiscellany.image`
---

`zhmiscellany.image.image_diff()`
---

`zhmiscellany.image.image_diff(img1, img2)`

Quantify the difference between 2 images, returns a float, lower means less difference.

#<|<image>|>

---
`zhmiscellany.list`
---

`zhmiscellany.list.subtract_lists()`
---

`zhmiscellany.list.subtract_lists(main_list, *other_lists)`

Subtract some lists from a main list.

#

`zhmiscellany.list.remove_duplicates_by_element()`
---

`zhmiscellany.list.remove_duplicates_by_element(tuple_list, element)`

Removes duplicates from a 2d list, takes an element for what to judge a duplicate by in the sub lists.

#

`zhmiscellany.list.remove_duplicates_by_element()`
---

`zhmiscellany.list.remove_duplicates_by_element(tuple_list, element)`

Removes duplicate tuples from a list based on a specific element index.

#

`zhmiscellany.list.multi_split()`
---

`zhmiscellany.list.multi_split(string_list, splits)`

Splits a list of strings multiple times using a list of delimiters, applying each split sequentially.

#<|<list>|>

---
`zhmiscellany.math`
---

`zhmiscellany.math.calculate_eta()`
---

`zhmiscellany.math.calculate_eta(timestamps, total_timestamps)`

Calculates the ETA of an event by a list of timestamps and an expected total amount of timestamps.

#

`zhmiscellany.math.smart_percentage()`
---

`zhmiscellany.math.smart_percentage(things, total_things)`

Returns a percentage that is automatically rounded to an appropriate amount of decimal points.

#

`zhmiscellany.math.calculate_evenly_spaced_points()`
---

`zhmiscellany.math.calculate_evenly_spaced_points(duration, segments)`

Calculates some evenly spaced numbers out of a larger number, for instance (5, 3) would be [0, 2.5, 5].

#

`zhmiscellany.math.clamp()`
---

`zhmiscellany.math.clamp(value, minimum, maximum)`

Clamps a value between 2 other values, (5, 2, 4) would return 4.

#

`zhmiscellany.math.generate_grid()`
---

`zhmiscellany.math.generate_grid(top_left, bottom_right, rows, cols, int_coords=True, row_major=True)`

Generates a grid of points between two coordinates with optional integer rounding and row-major ordering.

#

`zhmiscellany.math.generate_eased_points()`
---

`zhmiscellany.math.generate_eased_points(p1, p2, num_points)`

Generates interpolated points between two coordinates using an ease-in-out function for smooth transitions.

#

`zhmiscellany.math.generate_linear_points()`
---

`zhmiscellany.math.generate_linear_points(p1, p2, num_points)`

Generates interpolated points between two coordinates using linear spacing.

#

`zhmiscellany.math.round_to_min_digits()`
---

`zhmiscellany.math.round_to_min_digits(number, min_digits=3)`

Rounds a number while ensuring a minimum number of significant digits.

#<|<math>|>

---
`zhmiscellany.misc`
---

`zhmiscellany.misc.die()`
---

`zhmiscellany.misc.die()`

Kills the entire program, even if ran in a thread. Often useful.

#

`zhmiscellany.misc.get_actual_screen_resolution()`
---

`zhmiscellany.misc.get_actual_screen_resolution()`

Retrieves the actual screen resolution using the Windows API.

#

`zhmiscellany.misc.focus_window()`
---

`zhmiscellany.misc.focus_window(process_name, interval=0)`

Attempts to bring a window of the specified process into focus, with multiple fallback methods.

#

`zhmiscellany.misc.setup_console_window()`
---

`zhmiscellany.misc.setup_console_window(xy=(0, 0), wh=(400, 100), always_on_top=True)`

Configures the console window position, size, and always-on-top state.

#

`zhmiscellany.misc.show_progress()`
---

`zhmiscellany.misc.show_progress(things, total_things, extra_data="", smart_ratelimit=False, max_prints=1000)`

Displays a progress percentage, with optional smart rate limiting for large iterations.

#

`zhmiscellany.misc.every_nth()`
---

`zhmiscellany.misc.every_nth(number, n)`

Returns True if the number is a multiple of n.

#

`zhmiscellany.misc.smart_every_nth()`
---

`zhmiscellany.misc.smart_every_nth(number, n, total)`

Optimized variant of every_nth, ensuring final iteration is included.

#

`zhmiscellany.misc.calculate_eta()`
---

`zhmiscellany.misc.calculate_eta(timestamps, total_timestamps)`

Estimates time remaining based on timestamps and total expected entries.

#

`zhmiscellany.misc.decide()`
---

`zhmiscellany.misc.decide(options, text)`

Prompts user input constrained to predefined options.

#

`zhmiscellany.misc.import_module_from_path()`
---

`zhmiscellany.misc.import_module_from_path(path, module_name=None)`

Dynamically imports a Python module from a file path.

#

`zhmiscellany.misc.base62_hash()`
---

`zhmiscellany.misc.base62_hash(anything)`

Generates a base62 hash derived from the MD5 hash of the input.

#

`zhmiscellany.misc.md5_int_hash()`
---

`zhmiscellany.misc.md5_int_hash(anything)`

Generates an integer hash from the MD5 hash of the input.

#

`zhmiscellany.misc.high_precision_sleep()`
---

`zhmiscellany.misc.high_precision_sleep(duration)`

Performs precise sleeping using a busy-wait loop for high accuracy.

#

`zhmiscellany.misc.is_admin()`
---

`zhmiscellany.misc.is_admin()`

Checks if the current process is running with administrator privileges.

#

`zhmiscellany.misc.die_on_key()`
---

`zhmiscellany.misc.die_on_key(key="f9", show_message=False)`

Monitors a specific key press to terminate the process. Runs as a background thread.

#

`zhmiscellany.misc.obfuscate_python()`
---

`zhmiscellany.misc.obfuscate_python(python_code_string, do_not_obfuscate_indent_block_comment="# DNO", remove_prints=True, remove_comments=True, add_lines=True, new_line_ratio=10)`

Obfuscates Python code by removing comments, removing prints, and adding specially crafted junk lines that are impossible to remove. The functionality of code is unaffected, but it is rendered completely irreversibly unreadable.

#

`zhmiscellany.misc.time_it()`
---

`zhmiscellany.misc.time_it(action=False, clock=0)`

Measures and prints execution time for a given code section, supporting named timers.

#

`zhmiscellany.misc.here()`
---

`zhmiscellany.misc.here(*args)`

Prints debugging information including variable names, values, file name, and line number.

#

`zhmiscellany.misc.line()`
---

`zhmiscellany.misc.line`

Alias for the here() function, providing debug output.

#

`zhmiscellany.misc.l()`
---

`zhmiscellany.misc.l`

Alias for the here() function, providing debug output.

#<|<misc>|>

---
`zhmiscellany.netio`
---

`zhmiscellany.netio.download_file()`
---

`zhmiscellany.netio.download_file(url, file_path, ext)`

Downloads a file from a url to a file path, with an ext.

#

`zhmiscellany.netio.resolve_file()`
---

`zhmiscellany.netio.resolve_file(url, destination_folder=".")`

Generates a safe file path for a downloaded file by extracting its name from a URL and ensuring the path length is within limits.

#

`zhmiscellany.netio.generate_headers()`
---

`zhmiscellany.netio.generate_headers(url)`

Creates randomized HTTP headers for a given URL, including Referer and Host fields.

#<|<netio>|>

---
`zhmiscellany.processing`
---

`zhmiscellany.processing.multiprocess()`
---

`zhmiscellany.processing.multiprocess(target, args=(), max_retries=0, disable_warning=False)`

Runs a single function in a separate process using Ray multiprocessing.

#

`zhmiscellany.processing.synchronous_class_multiprocess()`
---

`zhmiscellany.processing.synchronous_class_multiprocess(cls, *args, disable_warning=False, **kwargs)`

Creates a remote Ray actor instance for a class, allowing parallel execution of class methods.

#

`zhmiscellany.processing.start_daemon()`
---

`zhmiscellany.processing.start_daemon(**kwargs)`

Starts a new daemon thread with the given parameters.

#

`zhmiscellany.processing.batch_multiprocess_threaded()`
---

`zhmiscellany.processing.batch_multiprocess_threaded(targets_and_args, disable_warning=False, killable=False, daemon=False)`

Executes multiple functions in parallel using Ray multiprocessing, and inside a thread as to be non-blocking.

#

`zhmiscellany.processing.multiprocess_threaded()`
---

`zhmiscellany.processing.multiprocess_threaded(target, args=(), disable_warning=False, killable=False, daemon=False)`

Runs a single function in a separate process and inside a thread as to be non-blocking.

#

`zhmiscellany.processing.raw_multiprocess()`
---

`zhmiscellany.processing.raw_multiprocess(func, args=(), fileless=True)`

Runs a function in a separate Python subprocess, capturing output while handling serialization and deserialization.

#

`zhmiscellany.processing.raw_continuous_multiprocess()`
---

`zhmiscellany.processing.raw_continuous_multiprocess(input_class, args=(), fileless=True, cleanup_file=True)`

Runs a class with a continuous output method in a separate subprocess, yielding results as they are produced.

#<|<processing>|>

---
`zhmiscellany.string`
---

`zhmiscellany.string.convert_to_base62()`
---

`zhmiscellany.string.convert_to_base62(number)`

Converts an integer to a base 62 number, this means all lower and upper letters, and numbers are used.

#

`zhmiscellany.string.get_universally_unique_string()`
---

`zhmiscellany.string.get_universally_unique_string()`

Returns a universally unique string, even if called directly sequentially. Strings are generated based off of time not randomness, as such it's impossible to get 2 that are the same.

#

`zhmiscellany.string.multi_replace()`
---

`zhmiscellany.string.multi_replace(string, replaces)`

Takes a string and a list of tuples, like (string, [(string1, string2)]) and in this instance replaces string1 in string with string2.

#

`zhmiscellany.string.timestamp_to_time()`
---

`zhmiscellany.string.timestamp_to_time(unix_timestamp)`

Takes a unix timestamp and returns the actual time as a string.

#

`zhmiscellany.string.truncate_string()`
---

`zhmiscellany.string.truncate_string(input_string, max_length)`

Truncates a string to a certain length.

#

`zhmiscellany.string.concatenate_strings_to_length()`
---

`zhmiscellany.string.concatenate_strings_to_length(strings, limit)`

Takes a list of strings and adds them together until adding any more would exceed the limit, then returns the resulting string.

#

`zhmiscellany.string.smart_round()`
---

`zhmiscellany.string.smart_round(number, decimals=0)`

Same as builtin "round" but removes any hanging .0 if it occurs.

#

`zhmiscellany.string.convert_bytes()`
---

`zhmiscellany.string.convert_bytes(size)`

Converts an int of bytes to a string like '8.3MB'.

#

`zhmiscellany.string.decide()`
---

`zhmiscellany.string.decide(options, text)`

Takes a list of options and a description text and makes the user decide between the options.

#

`zhmiscellany.string.filter_chars()`
---

`zhmiscellany.string.filter_chars(input_string, filter_string)`

Filters chars out of one string from a string of filter chars.

#

`zhmiscellany.string.multi_split()`
---

`zhmiscellany.string.multi_split(string, splits)`

`.split`s a string multiple times based on a list of strings to split by.

#<|<string>|>

---
`zhmiscellany.macro`
---

`zhmiscellany.macro.click_pixel()`
---

`def click_pixel(x=None, y=None, click_duration=None, right_click=False, middle_click=False, shift=False, ctrl=False, act_start=True, act_end=True, click_end_duration=None, double_click=False, animation_time=None, animation_fps=60, animation_easing=True, relative=False, ensure_movement=True, pre_click_duration=None, pre_click_wiggle=False):`

Simulates a mouse click at a given position using the raw SendInput method for better compatibility across applications. Supports right and middle clicks, modifier keys, and smooth animated movement with easing.

#

`zhmiscellany.macro.press_key()`
---

`zhmiscellany.macro.press_key(vk_code, shift=False, act_start=True, act_end=True, key_hold_time=0)`

Simulates a key press using the raw SendInput method. Supports holding shift and specifying key hold duration.

#

`zhmiscellany.macro.type_string()`
---

`zhmiscellany.macro.type_string(text=None, delay=None, key_hold_time=None, vk_codes=None, combine=False)`

Types a string or virtual key codes using the raw SendInput method. Supports per-character delays, key holding, and combined key presses.

#

`zhmiscellany.macro.scroll()`
---

`zhmiscellany.macro.scroll(amount, delay=None)`

Performs vertical scrolling using the raw SendInput method. Supports smooth scrolling with delay control.

#

`zhmiscellany.macro.get_mouse_xy()`
---

`zhmiscellany.macro.get_mouse_xy()`

Retrieves the current mouse cursor position.

#

`zhmiscellany.macro.KEY_CODES()`
---

`zhmiscellany.macro.KEY_CODES`

Dictionary mapping key names to their virtual key codes for use with press_key and type_string.

#<|<macro>|>

---
`zhmiscellany.cpp`
---

`zhmiscellany.cpp.subtract_lists()`
---

`zhmiscellany.cpp.subtract_lists(l1, l2)`

Subtracts l2 from l1 and returns l1. Much faster then any list subtraction possible in python alone.

#<|<cpp>|>

---
`zhmiscellany.rust`
---

`zhmiscellany.rust.numpy_mean()`
---

`zhmiscellany.rust.numpy_mean(l1)`

Gets the mean (average) of a numpy array, 10x faster than using numpy's built in mean.

#

`zhmiscellany.rust.numpy_median()`
---

`zhmiscellany.rust.numpy_median(l1)`

Gets the median of a numpy array, also 10x faster than using numpy's built in median.

#

`zhmiscellany.rust.numpy_sum()`
---

`zhmiscellany.rust.numpy_sum(l1)`

Gets the sum of a numpy array, 6x faster than using numpy's built in sum.

#

`zhmiscellany.rust.list_files_recursive()`
---

`zhmiscellany.rust.list_files_recursive(directory)`

Returns a list of absolute paths to all files in the directory and all subdirectories, is 5x faster than any non multiprocessing python implementation.

#<|<rust>|>

---
`zhmiscellany.pipes`
---

`zhmiscellany.pipes.PipeTransmitter()`
---

`zhmiscellany.pipes.PipeTransmitter(pipe_name, close_pipes=False)`

Creates a named pipe transmitter that sends data asynchronously using a background thread.

#

`zhmiscellany.pipes.PipeReceiver()`
---

`zhmiscellany.pipes.PipeReceiver(pipe_name)`

Creates a named pipe receiver that listens for incoming data asynchronously and supports a callback function for real-time processing.

#

`zhmiscellany.pipes.raw_receive_data()`
---

`zhmiscellany.pipes.raw_receive_data(pipe_name)`

Reads data from a named pipe synchronously, returning None if no data is available.

#

`zhmiscellany.pipes.raw_send_data()`
---

`zhmiscellany.pipes.raw_send_data(data, pipe_name)`

Sends data to a named pipe asynchronously using a background thread.

#<|<pipes>|>

---
`zhmiscellany.gui`
---

#<|<gui>|>