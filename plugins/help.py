from telethon import events


async def init(client) -> None:
    @client.on(events.NewMessage(pattern=r'(?i)/help$'))
    async def handler(event):
        await client.send_message(
            entity=event.peer_id,
            reply_to=event.reply_to_msg_id,
            message=f'/all - Тэгает всех пользователей канала. Доступно только админам.\n'
                    f'/alladmins - Тэгает всех админов канала\n'
                    f'/addGroupSchedule <Название группы> - '
                    f'Привязывает чат к каналу для расписании. Доступно только админам.\n'
                    f'/showSchedule - Показывает расписание на сегодня. Доступно только админам.\n'
                    f'/showTomSchedule - Показывает расписание на завтра. Доступно только админам.\n'
                    f'/deleteGroup - Отвязывает чат к каналу. Доступно только админам.')
