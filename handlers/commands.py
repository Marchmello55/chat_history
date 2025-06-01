from sqlalchemy.testing.suite.test_reflection import users
from telethon import events
from telethon.tl.types import Channel, PeerChannel
from database.models import create_database
import os

from utils.get_chat_history import process_chat_messages, process_chat_single_message
from config_data.client import client
from utils.deliter import delete_path
from database import requests as rq
from utils.zipper import async_zip_folder


@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Обработчик команды /start"""
    try:
        await event.reply('Для получения истории чата напишите команду /history ссылка_на_чат')
    except Exception as e:
        pass
        #print(f"Ошибка в start_command: {str(e)}")


@client.on(events.NewMessage(pattern='/history (.*)'))
async def history_command(event):
    """Обработчик команды /history"""
    try:
        sender = await event.get_sender()
        await del_files(sender.id, rq.FolderName.history)
        await create_database(rq.FolderName.history, str(sender.id))

        text = event.pattern_match.group(1)
        await event.reply(f"🔊 Вы указали: _{text}_", parse_mode='md')
        await process_chat_messages(client, sender, text)
    except Exception as e:
        await event.reply(f"Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern='/get_history'))
async def handle_get_history(event):
    """Обработчик команды /get_history"""
    try:
        sender = await event.get_sender()
        await del_files(sender.id, rq.FolderName.history)

        chat = await event.get_chat()
        chat_id = get_chat_id(chat)

        topic_id = None
        if event.message.reply_to and event.message.reply_to.reply_to_msg_id:
            topic_id = event.message.reply_to.reply_to_msg_id

        await event.reply(f"Начинаю обработку {'темы' if topic_id else 'чата'}...")
        await process_chat_messages(client, sender, chat_id, topic_id)

    except Exception as e:
        await event.reply(f"Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern="/wiretapping"))
async def handle_wiretapping(event):
    """Обработчик команды /wiretapping"""
    try:
        sender = await event.get_sender()
        await del_files(sender.id, rq.FolderName.wiretapping)

        chat = await event.get_chat()
        chat_id = get_chat_id(chat)

        topic_id = None
        if event.message.reply_to and event.message.reply_to.reply_to_msg_id:
            topic_id = event.message.reply_to.reply_to_msg_id

        data = {
            "tg_id": sender.id,
            "chat_id": chat_id,
            "topic_id": topic_id
        }

        await rq.add_chats(data)
        await event.reply(f"Начинаю прослушку {'темы' if topic_id else 'чата'}...")

    except Exception as e:
        await event.reply(f"Ошибка: {str(e)}")


@client.on(events.NewMessage(pattern="/get_wiretapping"))
async def handle_get_wiretapping(event):
    """Обработчик команды /get_wiretapping"""
    try:
        sender = await event.get_sender()

        if not await rq.get_user_tg_id(tg_id=sender.id):
            await event.reply("Вы не прослушиваете чаты")
            return

        for content_type in ['avatars', 'photo', 'file']:
            folder = f"{rq.FolderName.wiretapping}/{content_type}_{sender.id}"
            if os.path.exists(folder) and os.listdir(folder):
                zip_path = await async_zip_folder(folder)
                await client.send_file(sender.id, zip_path)
                os.remove(zip_path)

        db_path = f'database/{rq.FolderName.wiretapping}/{sender.id}.sqlite3'
        if os.path.exists(db_path):
            await client.send_file(sender.id, db_path)

    except Exception as e:
        await event.reply(f"Ошибка: {str(e)}")


@client.on(events.NewMessage())
async def handle_message(event):
    """Обработчик всех сообщений"""
    try:
        if not isinstance(event, events.NewMessage.Event):
            return

        sender = await event.get_sender()
        chat = await event.get_chat()
        chat_id = get_chat_id(chat)

        topic_id = None
        if event.message.reply_to and event.message.reply_to.reply_to_msg_id:
            topic_id = event.message.reply_to.reply_to_msg_id
        user = await rq.get_user_other_data(chat_id=chat_id, topic_id=topic_id)
        if not user: return
        chat_id_bd, topic_id_bd = user.chat_id, user.topic_id
        if chat_id_bd:
            if chat_id_bd == chat_id and topic_id_bd == topic_id:
                await process_chat_single_message(client, sender, chat_id, topic_id)

    except Exception as e:
        pass
        #print(f"Ошибка в handle_message: {str(e)}")


def get_chat_id(chat):
    """Получение ID чата с учетом его типа"""
    if isinstance(chat, (Channel, PeerChannel)):
        return -1000000000000 - chat.id if chat.id < 0 else chat.id
    return -chat.id if chat.id > 0 else chat.id


async def del_files(user_id: int, path: str):
    """Удаление файлов"""
    paths_to_delete = [
        f"{path}/avatars_{user_id}.zip",
        f"{path}/avatars_{user_id}",
        f"database/{path}/{user_id}.sqlite3",
        f"{path}/photo_{user_id}",
        f"{path}/photo_{user_id}.zip",
        f"{path}/file_{user_id}",
        f"{path}/file_{user_id}.zip"
    ]

    for path_to_delete in paths_to_delete:
        await delete_path(path_to_delete)