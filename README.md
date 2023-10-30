`zhmiscellany`,
===

a collection of miscellany functions/classes/modules made by me (zh).
---

[Introduction](https://github.com/zen-ham/zhmiscellany/tree/master#Introduction) \
[Usage examples](https://github.com/zen-ham/zhmiscellany/tree/master#Usageexamples) \
[Documentation](https://github.com/zen-ham/zhmiscellany/tree/master#Documentation)

---

Introduction
===

Can be installed with `pip install zhmiscellany`

The git repository for this package can be found [here](https://github.com/zen-ham/zhmiscellany). The docs also look nicer on github.

If you want to reach out, you may add my on discord at @z_h_ or join [my server](https://discord.gg/ThBBAuueVJ).

---

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

Documentation:
===

[zhmiscellany.discord](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanydiscord) Functions for interacting with discord in various ways.\
[zhmiscellany.fileio](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanyfileio) Functions for interacting with local files, such as json and other file related functions I find useful.\
[zhmiscellany.string](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanystring) Functions for interacting with/generating strings that I find useful.\
[zhmiscellany.math](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanymath) Functions for making some calculations easier.\
[zhmiscellany.netio](https://github.com/zen-ham/zhmiscellany/tree/master#zhmiscellanynetio) Internet related functions that didn't make sense in any other another module.

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