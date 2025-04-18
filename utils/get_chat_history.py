import os
from telethon.tl.types import User, ChatInviteAlready, ChatInvite
from telethon.errors import ChannelPrivateError, InviteHashExpiredError
from telethon.tl.functions.channels import JoinChannelRequest

from database import requests as rq
from utils.zipper import async_zip_folder


async def process_chat_messages(client, user, chat_identifier):
    """
    Обрабатывает сообщения чата с начала (от старых к новым)
    """
    # Создаем папки для данных
    os.makedirs(f'avatars_{user.id}', exist_ok=True)
    os.makedirs(f'photo_{user.id}', exist_ok=True)
    os.makedirs(f'file_{user.id}', exist_ok=True)


    try:
        # Получаем информацию о чате
        try:
            chat = await client.get_entity(chat_identifier)
        except (ValueError, ChannelPrivateError):
            if isinstance(chat_identifier, str) and ('t.me' in chat_identifier or 'telegram.me' in chat_identifier):
                await client.send_message(user.id, f"Пытаюсь присоединиться к чату по ссылке: {chat_identifier}")
                try:
                    result = await client(JoinChannelRequest(chat_identifier))
                    if isinstance(result, ChatInviteAlready):
                        chat = result.chat
                    elif isinstance(result, ChatInvite):
                        chat = result.chat
                        await client.send_message(user.id, f"Успешно присоединился к новому чату: {chat.title}")
                    else:
                        await client.send_message(user.id, "Не удалось распознать результат присоединения")
                        return
                except InviteHashExpiredError:
                    await client.send_message(user.id, "Ссылка-приглашение недействительна или истекла")
                    return
                except Exception as e:
                    await client.send_message(user.id, f"Ошибка при присоединении: {e}")
                    return
            else:
                await client.send_message(user.id, "Чат не найден и не предоставлена валидная ссылка-приглашение")
                return

        # Получаем общее количество сообщений
        total_messages = await client.get_messages(chat, limit=1)
        if total_messages:
            await client.send_message(user.id, f"\nВсего сообщений в чате: {total_messages[0].id}")

        # Обрабатываем сообщения в хронологическом порядке
        message_count = 0
        async for message in client.iter_messages(chat, reverse=True):  # reverse=True для порядка от старых к новым
            await process_message(client, message, user, message_count)
            message_count += 1

        await client.send_message(user.id, f"\nОбработка завершена. Обработано сообщений: {message_count}")

        # Архивируем и отправляем файлы
        zip_path = await async_zip_folder(f"avatars_{user.id}")
        await client.send_file(user.id, zip_path)
        await client.send_file(user.id, await async_zip_folder(f"photo_{user.id}"))
        await client.send_file(user.id, await async_zip_folder(f"file_{user.id}"))
        await client.send_file(user.id, f'database/{user.id}.sqlite3')

    except Exception as e:
        await client.send_message(user.id, f"Критическая ошибка: {e}")


async def process_message(client, message, user, message_count):
    """Обрабатывает одно сообщение"""
    try:
        # Информация об отправителе
        sender = await message.get_sender()
        if not sender or not isinstance(sender, User):
            return

        user_info = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
        data = {
            "id_message": message.id,
            "tg_id": sender.id,
            "username": user_info,
            "date": message.date.strftime('%Y-%m-%d %H:%M:%S'),
            "text": message.text or ""
        }

        # Скачиваем аватар
        avatar_path = await download_avatar(client, user, sender)
        if avatar_path:
            data["avatar"] = avatar_path

        # Обработка фото
        if message.photo:
            photo_path = await download_photo(client, user, message)
            if photo_path:
                data["photo_path"] = photo_path

        # Обработка файлов (документов)
        if message.document:
            file_path = await download_file(client, user, message)
            if file_path:
                data["file_path"] = file_path
                data["file_name"] = message.document.attributes[0].file_name if hasattr(message.document,
                                                                                        'attributes') else "unknown"

        await rq.add_user(db_name=str(user.id), data=data)

    except Exception as e:
        print(f"Ошибка обработки сообщения: {e}")
        await client.send_message(user.id, f"Ошибка при обработке сообщения {message_count}: {e}")


async def download_photo(client, user, message):
    """Скачивает фото из сообщения"""
    try:
        photo_dir = f"photo_{user.id}"
        os.makedirs(photo_dir, exist_ok=True)

        # Формируем уникальное имя файла
        file_name = f"{message.id}_{message.date.timestamp()}.jpg"
        photo_path = os.path.join(photo_dir, file_name)

        if not os.path.exists(photo_path):
            await client.download_media(message.photo, file=photo_path)

        return os.path.abspath(photo_path)
    except Exception as e:
        print(f"Ошибка скачивания фото: {e}")
        return None


async def download_file(client, user, message):
    """Скачивает файл из сообщения"""
    try:
        file_dir = f"file_{user.id}"
        os.makedirs(file_dir, exist_ok=True)

        # Получаем оригинальное имя файла
        file_name = None
        if hasattr(message.document, 'attributes'):
            for attr in message.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    break

        if not file_name:
            file_name = f"file_{message.id}_{message.date.timestamp()}"

        file_path = os.path.join(file_dir, file_name)

        if not os.path.exists(file_path):
            await client.download_media(message.document, file=file_path)

        return os.path.abspath(file_path)
    except Exception as e:
        print(f"Ошибка скачивания файла: {e}")
        return None

async def download_avatar(client, user, sender):
    """Скачивает аватар пользователя с обработкой ошибок"""
    try:
        avatar_path = f"avatars_{user.id}/{sender.id}.jpg"
        if not os.path.exists(avatar_path):
            await client.download_profile_photo(sender, file=avatar_path)
        return os.path.abspath(avatar_path)
    except Exception as e:
        print(f"Ошибка скачивания аватара: {e}")
        return None
