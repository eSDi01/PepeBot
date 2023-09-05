# -*- coding: cp1251 -*-
import asyncio
import os
import sys

from pathlib import Path
from dotenv import load_dotenv

from telethon.sync import TelegramClient

import plugins.schedule as schedule

try:
    import plugins
except ImportError:
    try:
        from . import plugins
    except ImportError:
        print('could not load the plugins module, does the directory exist '
              'in the correct location?', file=sys.stderr)

        exit(1)

BASE_DIR = Path(__file__).resolve().parent

dotenv_path = os.path.join(BASE_DIR, '.env')

if not os.getenv('ACTIONS'):
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        with open('.env', 'w') as env:
            env.write('API_ID=\n'
                      'API_HASH=\n'
                      'TOKEN=')
        raise Exception('You need to fill in the .env file')

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
TOKEN = os.getenv('TOKEN')
NAME = TOKEN.split(':')[0]


async def main():
    client = TelegramClient(NAME, API_ID, API_HASH)

    await client.start(bot_token=TOKEN)

    try:
        await plugins.init(client)
        await client.run_until_disconnected()
    finally:
        await client.disconnect()


if __name__ == '__main__':
    schedule.main()
    asyncio.run(main())
