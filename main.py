# -*- coding: cp1251 -*-
from telethon.sync import TelegramClient, events
from telethon.tl.custom.message import Message

api_id = ''
api_hash = ''
token = ''

client = TelegramClient('name', api_id, api_hash).start(bot_token=token)


@client.on(events.NewMessage(pattern='/all'))
async def handler(event):
    sender = await event.get_sender()

    channel = await event.get_chat()
    users = client.iter_participants(channel)
    answ = ''
    i = 0
    mention = ''
    async for user in users:
        if not user.bot:
            i += 1
            if user.username:
                mention += f'[@{user.username}](tg://user?id={user.id}) '
            else:
                mention += f'[@{user.first_name}](tg://user?id={user.id}) '
            if i >= 5:
                mention = mention.rstrip()
                await client.send_message(
                    entity=event.peer_id,
                    message=mention)
                i = 0
                mention = ''
    if mention != '':
        mention = mention.rstrip()
        await client.send_message(
            entity=event.peer_id,
            message=mention)


@client.on(events.NewMessage(pattern='/test'))
async def handler(event: Message):
    sender = await event.message.from_id.user_id
    print(sender)
    channel = await event.get_chat()


client.run_until_disconnected()

