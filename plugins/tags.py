from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins


async def create_list_users(users) -> list[str]:
    tags: list = []
    async for user in users:
        if not user.bot:
            if user.username:
                tags.append(f'[@{user.username}](tg://user?id={user.id})')
            else:
                tags.append(f'[@{user.first_name}](tg://user?id={user.id})')
    return tags


async def send_tags(client, event, tags) -> None:
    for i in range(0, len(tags), 5):
        msg = ' '.join(tags[i:i + 5])
        await client.send_message(
            entity=event.peer_id,
            message=msg)


async def init(client) -> None:
    @client.on(events.NewMessage(pattern=r'(?i)/all$'))
    async def handler(event):
        sender_id = event.message.from_id.user_id
        channel = await event.get_chat()
        admins_ids = [admin.id async for admin in client.iter_participants(channel, filter=ChannelParticipantsAdmins)]

        if (sender_id in admins_ids) and not event.sender.bot:
            users = client.iter_participants(channel)
            await send_tags(client, event, await create_list_users(users))

    @client.on(events.NewMessage(pattern=r'(?i)/allAdmins$'))
    async def handler(event):
        channel = await event.get_chat()

        if not event.sender.bot:
            users = client.iter_participants(channel, filter=ChannelParticipantsAdmins)
            await send_tags(client, event, await create_list_users(users))
