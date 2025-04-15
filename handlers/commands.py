from telethon import events
from database.models import create_database

from utils.get_chat_history import process_chat_messages
from config_data.client import client
from utils.deliter import delete_path

@events.register(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.reply('Для получения истории чата напишити комманду /history ссылка на чат')


@events.register(events.NewMessage(pattern='/history (.*)'))
async def history_command(event):
    sender = await event.get_sender()
    await delete_path(f"avatars_{str(sender.id)}.zip")
    await delete_path(f"avatars_{str(sender.id)}")
    await delete_path(f"database/{str(sender.id)}.sqlite3")
    await create_database(sender.id)
    text = event.pattern_match.group(1)
    await event.reply(f"🔊 Вы сказали: _{text}_", parse_mode='md')
    await process_chat_messages(client, sender, text)
