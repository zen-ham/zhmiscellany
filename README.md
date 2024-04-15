`zhmiscellany`,
===

An organized collection of unique and useful functions/classes/modules.
---

[Introduction](https://github.com/zen-ham/zhmiscellany/tree/master#Introduction) \
[Documentation](https://github.com/zen-ham/zhmiscellany/tree/master#Documentation) \
[Usage examples](https://github.com/zen-ham/zhmiscellany/tree/master#Usage-examples)

---

Introduction
===

Can be installed with `pip install zhmiscellany`

The git repository for this package can be found [here](https://github.com/zen-ham/zhmiscellany). The docs also look nicer on github.

If you wish to reach out, you may add @z_h_ on Discord, or join [the server](https://discord.gg/ThBBAuueVJ).

---

Documentation:
===

[Usage-examples](https://github.com/zen-ham/zhmiscellany/blob/master/README.md#usage-examples) Usage examples.\
[zhmiscellany.discord](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanydiscord) Functions for interacting with discord in various ways.\
[zhmiscellany.fileio](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyfileio) Functions for interacting with local files, such as json and other file related functions I find useful.\
[zhmiscellany.string](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanystring) Functions for interacting with/generating strings that I find useful.\
[zhmiscellany.math](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanymath) Functions for making some calculations easier.\
[zhmiscellany.netio](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanynetio) Internet related functions that didn't make sense in any other module.\
[zhmiscellany.image](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyimage) Functions for quantifying and manipulating images.\
[zhmiscellany.list](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanylist) Functions for manipulating lists.\
[zhmiscellany.dict](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanydict) Functions for working with dicts.\
[zhmiscellany.processing](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyprocessing) Functions for processing data in threads in a more straight forward way.\
[zhmiscellany.misc](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanymisc) Miscellaneous functions that didn't fit anywhere else.\
[zhmiscellany.pipes](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanypipes) A pair of classes for effectively using pipes for IPC (Inter-Process Communication)


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

`zhmiscellany.discord`:
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

Gets info about the local user, allows code to be run without needing to find your damn user token every time.\
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

#

`zhmiscellany.dict`
---

`zhmiscellany.dict.print_dict()`
---

`zhmiscellany.dict.print_dict(ldict)`

Prints out a dict in a readable way.

#

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

---
`zhmiscellany.image`
---

`zhmiscellany.image.image_diff()`
---

`zhmiscellany.image.image_diff(img1, img2)`

Quantify the difference between 2 images, returns a float, lower means less difference.

#

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

---
`zhmiscellany.misc`
---

`zhmiscellany.misc.die()`
---

`zhmiscellany.misc.die()`

Kills the entire program, even if ran in a thread. Often useful.

#

`zhmiscellany.misc.set_activity_timeout()`
---

`zhmiscellany.misc.set_activity_timeout(timeout)`

Sets the timeout for how long the program should wait without an activity before closing.

#

`zhmiscellany.misc.activity()`
---

`zhmiscellany.misc.activity()`

Signifies an activity to the timeout.

#

---
`zhmiscellany.netio`
---

`zhmiscellany.netio.download_file()`
---

`zhmiscellany.netio.download_file(url, file_path, ext)`

Downloads a file from a url to a file path, with an ext.

#

---
`zhmiscellany.processing`
---
`zhmiscellany.processing.batch_threading()`
---

`zhmiscellany.processing.batch_threading(targets, threads)`

Takes a list of functions and arguments, for instance [(print_numbers_up_to, 8), (print_numbers_up_to, 11)]

#

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

Returns a universally unique string.

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
