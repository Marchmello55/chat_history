import os
from telethon import events

from handlers import commands
from config_data.client import client
from config_data.config import Config, load_config
from database import requests as rq

config: Config = load_config()


async def main():
    # Авторизуемся как пользователь
    await client.start(phone=config.tg_bot.phone)
    print(f"{config.tg_bot.bot_name} запущен...")
    os.makedirs(f'{str(rq.FolderName.history)}', exist_ok=True)
    os.makedirs(f'{str(rq.FolderName.wiretapping)}', exist_ok=True)


    # Добавляем обработчики
    client.add_event_handler(commands.start_command)
    client.add_event_handler(commands.history_command)
    client.add_event_handler(commands.handle_get_history)
    client.add_event_handler(commands.handle_wiretapping)
    client.add_event_handler(commands.handle_get_wiretapping)
    client.add_event_handler(commands.handle_message, events.NewMessage)

    # Оставляем клиент работать
    await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())