import os
from telethon.tl.types import User, ChatInviteAlready, ChatInvite, DocumentAttributeAudio
from telethon.errors import ChannelPrivateError, InviteHashExpiredError
from telethon.tl.functions.channels import JoinChannelRequest

from database import requests as rq
from utils.zipper import async_zip_folder


async def process_chat_messages(client, user, chat_identifier, topic_id=None):
    """
    Обрабатывает сообщения чата или темы с начала (от старых к новым)

    :param client: Telethon клиент
    :param user: Пользователь, которому отправляем результаты
    :param chat_identifier: ID/username чата или ссылка (обязательный)
    :param topic_id: ID темы (None для обработки всего чата)
    """
    if chat_identifier is None:
        await client.send_message(user.id, "Ошибка: не указан идентификатор чата")
        return

    # Создаем папки для данных
    os.makedirs(f'{rq.FolderName.history}/avatars_{user.id}', exist_ok=True)
    os.makedirs(f'{rq.FolderName.history}/photo_{user.id}', exist_ok=True)
    os.makedirs(f'{rq.FolderName.history}/file_{user.id}', exist_ok=True)

    try:
        # Получаем информацию о чате
        try:
            if isinstance(chat_identifier, (int, str)):
                chat = await client.get_entity(chat_identifier)
            else:
                await client.send_message(user.id, "Неверный формат идентификатора чата")
                return
        except (ValueError, ChannelPrivateError):
            if isinstance(chat_identifier, str) and ('t.me' in chat_identifier or 'telegram.me' in chat_identifier):
                await client.send_message(user.id, f"Пытаюсь присоединиться к чату по ссылке: {chat_identifier}")
                try:
                    result = await client(JoinChannelRequest(chat_identifier))
                    if isinstance(result, (ChatInviteAlready, ChatInvite)):
                        chat = result.chat
                        if isinstance(result, ChatInvite):
                            await client.send_message(user.id, f"Успешно присоединился к новому чату: {chat.title}")
                    else:
                        await client.send_message(user.id, "Не удалось распознать результат присоединения")
                        return
                except InviteHashExpiredError:
                    await client.send_message(user.id, "Ссылка-приглашение недействительна или истекла")
                    return
                except Exception as e:
                    await client.send_message(user.id, f"Ошибка при присоединении: {str(e)}")
                    return
            else:
                await client.send_message(user.id, "Чат не найден и не предоставлена валидная ссылка-приглашение")
                return
        except Exception as e:
            await client.send_message(user.id, f"Ошибка получения информации о чате: {str(e)}")
            return

        if not hasattr(chat, 'id'):
            await client.send_message(user.id, "Не удалось получить ID чата")
            return

        # Получаем сообщения
        try:
            total_messages = await client.get_messages(
                chat,
                limit=1,
                reply_to=topic_id if topic_id else None
            )

            if total_messages:
                msg_type = "темы" if topic_id else "чата"
                await client.send_message(user.id, f"\nВсего сообщений в {msg_type}: {total_messages[0].id}")

            message_count = 0
            async for message in client.iter_messages(
                    chat,
                    reverse=True,
                    reply_to=topic_id if topic_id else None
            ):
                if message:
                    await process_message(rq.FolderName.history, client, message, user, message_count, str(user.id))
                    message_count += 1

            msg_type = "темы" if topic_id else "чата"
            await client.send_message(user.id,
                                      f"\nОбработка {msg_type} завершена. Обработано сообщений: {message_count}")

        except Exception as e:
            await client.send_message(user.id, f"Ошибка при получении сообщений: {str(e)}")
            return

        # Архивирование
        try:
            for content_type in ['avatars', 'photo', 'file']:
                folder = f"{rq.FolderName.history}/{content_type}_{user.id}"
                if os.path.exists(folder) and os.listdir(folder):
                    zip_path = await async_zip_folder(folder)
                    await client.send_file(user.id, zip_path)
                    os.remove(zip_path)

            db_path = f'database/{rq.FolderName.history}/{user.id}.sqlite3'
            if os.path.exists(db_path):
                await client.send_file(user.id, db_path)

        except Exception as e:
            await client.send_message(user.id, f"Ошибка при архивировании данных: {str(e)}")

    except Exception as e:
        await client.send_message(user.id, f"Критическая ошибка: {str(e)}")


async def process_chat_single_message(client, user, chat_identifier, topic_id=None):
    """
    Обрабатывает одно сообщение из чата или темы

    :param client: Telethon клиент
    :param user: Пользователь, которому отправляем результаты
    :param chat_identifier: ID/username чата или ссылка
    :param topic_id: ID темы (None для всего чата)
    """
    if chat_identifier is None:
        await client.send_message(user.id, "Ошибка: не указан идентификатор чата")
        return

    # Создаем папки для данных
    os.makedirs(f'{rq.FolderName.wiretapping}/avatars_{user.id}', exist_ok=True)
    os.makedirs(f'{rq.FolderName.wiretapping}/photo_{user.id}', exist_ok=True)
    os.makedirs(f'{rq.FolderName.wiretapping}/file_{user.id}', exist_ok=True)

    try:
        # Получаем информацию о чате
        try:
            if isinstance(chat_identifier, (int, str)):
                chat = await client.get_entity(chat_identifier)
            else:
                await client.send_message(user.id, "Неверный формат идентификатора чата")
                return
        except (ValueError, ChannelPrivateError) as e:
            if isinstance(chat_identifier, str) and ('t.me' in chat_identifier or 'telegram.me' in chat_identifier):
                await client.send_message(user.id, f"Пытаюсь присоединиться к чату по ссылке: {chat_identifier}")
                try:
                    result = await client(JoinChannelRequest(chat_identifier))
                    if isinstance(result, (ChatInviteAlready, ChatInvite)):
                        chat = result.chat
                        if isinstance(result, ChatInvite):
                            await client.send_message(user.id, f"Успешно присоединился к новому чату: {chat.title}")
                    else:
                        await client.send_message(user.id, "Не удалось распознать результат присоединения")
                        return
                except InviteHashExpiredError:
                    await client.send_message(user.id, "Ссылка-приглашение недействительна или истекла")
                    return
                except Exception as e:
                    await client.send_message(user.id, f"Ошибка при присоединении: {str(e)}")
                    return
            else:
                await client.send_message(user.id, "Чат не найден и не предоставлена валидная ссылка-приглашение")
                return
        except Exception as e:
            await client.send_message(user.id, f"Ошибка получения информации о чате: {str(e)}")
            return

        if not hasattr(chat, 'id'):
            await client.send_message(user.id, "Не удалось получить ID чата")
            return

        # Получаем последнее сообщение
        messages = await client.get_messages(
            chat,
            limit=1,
            reply_to=topic_id if topic_id else None
        )

        if messages:
            await process_single_message(client, messages[0], user, str(user.id))

    except Exception as e:
        await client.send_message(user.id, f"Критическая ошибка: {str(e)}")


async def process_message(folder_name, client, message, user, message_count, folder_suffix):
    """Обрабатывает одно сообщение"""
    try:
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
        avatar_path = await download_avatar(client, folder_name, folder_suffix, sender)
        if avatar_path:
            data["avatar"] = avatar_path

        # Обработка медиа
        if message.photo:
            photo_path = await download_photo(client, folder_name, folder_suffix, message)
            if photo_path:
                data["media"] = photo_path

        if message.document:
            file_path, _ = await download_file(client, folder_name, folder_suffix, message)
            if file_path:
                data["file"] = file_path

        await rq.add_user(folder_name=folder_name, db_name=str(user.id), data=data)

    except Exception as e:
        await client.send_message(user.id, f"Ошибка при обработке сообщения {message_count}: {str(e)}")


async def process_single_message(client, message, user, folder_suffix, folder_name=rq.FolderName.wiretapping):
    """Обрабатывает одно новое сообщение"""
    try:
        sender = await message.get_sender()
        if not sender or not isinstance(sender, User):
            return

        data = {
            "id_message": message.id,
            "tg_id": sender.id,
            "username": f"{sender.first_name or ''} {sender.last_name or ''}".strip(),
            "date": message.date.strftime('%Y-%m-%d %H:%M:%S'),
            "text": message.text or ""
        }

        avatar_path = await download_avatar(client, folder_name, folder_suffix, sender)
        if avatar_path:
            data["avatar"] = avatar_path

        if message.photo:
            data["photo"] = await download_photo(
                client=client,
                path=folder_name,
                folder_suffix=folder_suffix,
                message=message
            )

        if message.document:
            file_path, _ = await download_file(
                client=client,
                path=folder_name,
                folder_suffix=folder_suffix,
                message=message
            )
            if file_path:
                data["file"] = file_path

        await rq.add_user(folder_name=folder_name, db_name=str(user.id), data=data)
    except Exception as e:
        print(f"Ошибка обработки сообщения {message.id}: {str(e)}")
        raise


async def download_photo(client, path, folder_suffix, message):
    """Скачивает фото из сообщения"""
    try:
        photo_dir = f"{path}/photo_{folder_suffix}"
        os.makedirs(photo_dir, exist_ok=True)

        file_name = f"{message.id}_{int(message.date.timestamp())}.jpg"
        photo_path = os.path.join(photo_dir, file_name)

        if not os.path.exists(photo_path):
            await client.download_media(message.photo, file=photo_path)

        return os.path.abspath(photo_path)
    except Exception as e:
        print(f"Ошибка скачивания фото: {str(e)}")
        return None


async def download_file(client, path, folder_suffix, message):
    """Скачивает файл из сообщения"""
    try:
        file_dir = f"{path}/file_{folder_suffix}"
        os.makedirs(file_dir, exist_ok=True)

        file_name = None
        if hasattr(message.document, 'attributes'):
            for attr in message.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    break
                elif isinstance(attr, DocumentAttributeAudio):
                    file_name = f"audio_{message.id}_{int(message.date.timestamp())}.mp3"

        if not file_name:
            ext = message.document.mime_type.split('/')[-1] if message.document.mime_type else 'bin'
            file_name = f"file_{message.id}_{int(message.date.timestamp())}.{ext}"

        file_path = os.path.join(file_dir, file_name)

        if not os.path.exists(file_path):
            await client.download_media(message.document, file=file_path)

        return os.path.abspath(file_path), file_name
    except Exception as e:
        print(f"Ошибка скачивания файла: {str(e)}")
        return None, None


async def download_avatar(client, path, folder_suffix, sender):
    """Скачивает аватар пользователя"""
    try:
        avatar_dir = f"{path}/avatars_{folder_suffix}"
        os.makedirs(avatar_dir, exist_ok=True)

        avatar_path = os.path.join(avatar_dir, f"{sender.id}.jpg")

        if not os.path.exists(avatar_path):
            await client.download_profile_photo(sender, file=avatar_path)

        return os.path.abspath(avatar_path) if os.path.exists(avatar_path) else None
    except Exception as e:
        print(f"Ошибка скачивания аватара: {str(e)}")
        return None