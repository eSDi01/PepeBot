import asyncio
import os

import pickle
import time

import requests
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.client.telegramclient import TelegramClient
from telethon.tl.custom.button import Button


def load_file():
    channel_group = {}

    base_dir = Path(__file__).resolve().parent.parent

    channel_group_path = os.path.join(base_dir, 'channel_group.dat')

    if os.path.exists(channel_group_path):
        with open(channel_group_path, 'rb') as file:
            reader = pickle.load(file)
            channel_group = reader
    else:
        with open(channel_group_path, 'wb') as file:
            pickle.dump(dict(), file)

    return channel_group


def save_file(channel_group):
    base_dir = Path(__file__).resolve().parent.parent
    channel_group_path = os.path.join(base_dir, 'channel_group.dat')

    with open(channel_group_path, 'wb') as file:
        pickle.dump(channel_group, file)


# def alarm():
#     while True:
#         now = datetime.now()
#
#         hour = now.hour
#         minute = now.minute
#         second = now.second
#
#         if minute % 60 == 0 and second % 60 == 0:
#             pass


async def init(client: TelegramClient):
    @client.on(events.NewMessage(pattern=r'(?i)/addGroupSchedule\b'))
    async def handler(event):
        channel_group = load_file()

        sender_id = event.message.from_id.user_id
        sender = await client.get_entity(sender_id)

        channel = await event.get_chat()

        admins = client.iter_participants(channel, filter=ChannelParticipantsAdmins())

        is_admin = False

        async for admin in admins:
            if sender_id == admin.id:
                is_admin = True
                break

        if is_admin and not sender.bot:
            msg = event.message.message
            while "  " in msg:
                msg = msg.replace("  ", " ")

            if len(msg.split(' ', 1)) > 1:
                search = msg.split(' ', 1)[1]
                search_url = quote_plus(search)
                r = requests.get(
                    f'https://rasp.omgtu.ru/api/search?term={search_url}&type=group')
                json_group = r.json()
                if len(json_group) > 0:
                    buttons = []
                    for i in range(0, len(json_group) if len(json_group) <= 5 else 5):
                        group_id = json_group[i]['id']
                        if str(channel) in channel_group:
                            if str(group_id) in channel_group[str(channel)]:
                                continue
                        buttons.append([Button.inline(json_group[i]['label'],
                                                      f'g{group_id}:{json_group[i]["label"]}')])
                    buttons.append([Button.inline('Отмена', b'cansel')])
                    await client.send_message(
                        entity=event.peer_id,
                        reply_to=event.reply_to_msg_id,
                        message='Выберите группу:',
                        buttons=buttons)
                else:
                    result = await client.send_message(
                        entity=event.peer_id,
                        reply_to=event.reply_to_msg_id,
                        message='Не найдено ни одной группы')
                    asyncio.create_task(sleep_del(channel, result.id))
            else:
                result = await client.send_message(
                    entity=event.peer_id,
                    reply_to=event.reply_to_msg_id,
                    message='Команда не соответствует конструкции\n' 
                            '/addgroupschedule <Название группы>')
                asyncio.create_task(sleep_del(channel, result.id))

    async def sleep_del(channel, msg_id):
        time.sleep(3)
        await client.delete_messages(entity=channel.id, message_ids=msg_id)

    @client.on(events.CallbackQuery())
    async def iquery(event):
        channel_group = load_file()

        sender_id = event.sender.id
        channel = await event.get_chat()
        admins_ids = [admin.id async for admin in client.iter_participants(channel, filter=ChannelParticipantsAdmins())]

        data = event.data.decode('UTF-8')
        if data[0] == 'g' and sender_id in admins_ids:
            group_id = data.split(':')[0][1:]
            group_name = data.split(':')[1]

            if not str(channel.id) in channel_group:
                channel_group[str(channel.id)] = dict()
            channel_group[str(channel.id)][group_id] = group_name

            await client.delete_messages(entity=channel.id, message_ids=event.message_id)
            save_file(channel_group)

        if data[0] == 'd' and sender_id in admins_ids:
            group_id = data.split(':')[0][1:]
            del channel_group[str(channel.id)][group_id]
            if len(channel_group[str(channel.id)]) > 0:
                del channel_group[str(channel.id)]

            await client.delete_messages(entity=channel.id, message_ids=event.message_id)
            save_file(channel_group)

        if data == 'cansel' and sender_id in admins_ids:
            await client.delete_messages(entity=channel.id, message_ids=event.message_id)

    @client.on(events.NewMessage(pattern=r'(?i)/showSchedule\b'))
    async def handler(event):
        today = date.today()

        await show_schedule(client, event, today)

    @client.on(events.NewMessage(pattern=r'(?i)/showTomSchedule\b'))
    async def handler(event):
        today = date.today()

        await show_schedule(client, event, f_tom(today))

    @client.on(events.NewMessage(pattern=r'(?i)/deleteGroup\b'))
    async def handler(event):
        sender_id = event.message.from_id.user_id
        channel = await event.get_chat()
        admins_ids = [admin.id async for admin in client.iter_participants(channel, filter=ChannelParticipantsAdmins())]

        if (sender_id in admins_ids) and not event.sender.bot:
            channel_group = load_file()
            buttons = []
            for group_id, group_name in channel_group[str(channel.id)].items():
                buttons.append([Button.inline(group_name, f'd{group_id}:{group_name}')])
            if len(buttons) > 0:
                buttons.append([Button.inline('Отмена', b'cansel')])
                await client.send_message(
                    entity=event.peer_id,
                    reply_to=event.reply_to_msg_id,
                    message='Выберите группу:',
                    buttons=buttons)
            else:
                result = await client.send_message(
                    entity=event.peer_id,
                    reply_to=event.reply_to_msg_id,
                    message='Не найдено ни одной группы')
                asyncio.create_task(sleep_del(channel, result.id))


async def show_schedule(client, event, day):
    sender_id = event.message.from_id.user_id
    channel = await event.get_chat()
    admins_ids = [admin.id async for admin in client.iter_participants(channel, filter=ChannelParticipantsAdmins)]

    if (sender_id in admins_ids) and not event.sender.bot:
        channel_group = load_file()

        if day.isoweekday() > 6:
            day = f_tom(day)

        start_week = day - timedelta(days=day.weekday())
        end_week = start_week + timedelta(days=6)

        msg = ''

        if str(channel.id) in channel_group:
            for group in channel_group[str(channel.id)]:
                r = requests.get(
                    f'https://rasp.omgtu.ru/api/schedule/group/{group}?' +
                    f'start={start_week.year}.{start_week.strftime("%m")}.' +
                    f'{start_week.strftime("%d")}&finish={end_week.year}.' +
                    f'{end_week.strftime("%m")}.{end_week.strftime("%d")}&lng=1')
                json = r.json()

                schedule = [lesson for lesson in json if date_comparison(day, lesson)]

                lesson_count = 0

                for i in range(len(schedule)):
                    msg, lesson_count = display_separators(msg, i, lesson_count, schedule)

        while "  " in msg:
            msg = msg.replace("  ", " ")

        await client.send_message(
            entity=event.peer_id,
            reply_to=event.reply_to_msg_id,
            message=msg)


def text_lesson(json_lesson):
    return f'\U0001F552{json_lesson["beginLesson"]}-{json_lesson["endLesson"]}\n\n' \
           f'\U0001F465{json_lesson["group"] or json_lesson["subGroup"] or "Поток"}\n' \
           f'\U0001F4DD{json_lesson["discipline"]} ({json_lesson["kindOfWork"]})\n' \
           f'\U0001F6AA{json_lesson["auditorium"]} ({json_lesson["building"]})\n' \
           f'\U0001F464{json_lesson["lecturer"]}\n'


def display_separators(msg, i, lesson_count, schedule):
    if i < 1:
        msg += f'\U0001F4C5{schedule[i]["date"]}, {schedule[i]["dayOfWeekString"]}\t\U0001F494\n\n'

    if schedule[i]['contentTableOfLessonsOid'] != lesson_count:
        if i >= 1:
            msg += f'====================================================\n\n'
        lesson_count = schedule[i]['contentTableOfLessonsOid']
        msg += text_lesson(schedule[i])
    else:
        msg += f'----------------------------------------------------' \
               f'----------------------------------------------------\n' \
               f'{text_lesson(schedule[i])}'
    return msg, lesson_count


def f_tom(f_today) -> date:
    tomorrow = f_today + timedelta(days=1)
    return date(tomorrow.year, tomorrow.month, tomorrow.day)


def date_comparison(f_today, json) -> bool:
    return json['date'] == f'{f_today.year}.{f_today.strftime("%m")}.{f_today.strftime("%d")}'
