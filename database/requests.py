from database.models import create_database, create_database_for_chats, User_chat
from dataclasses import dataclass
from database.models import User
import logging
from sqlalchemy import select, update

@dataclass
class FolderName:
    history = "history"
    wiretapping = "wiretapping"
    users = "users"

async def add_user(folder_name: str ,db_name: str, data: dict) -> None:
    """
    добавление людей из чата
    """
    logging.info(f'add_user')
    async_session = await create_database(folder_name ,db_name)
    async with async_session() as session:
        session.add(User(**data))
        await session.commit()


async def add_chats(data: dict, db_name: str = FolderName.users) -> None:
    """
    добавление пользователей с чатами и темами
    """
    logging.info(f'add_chats')
    async_session = await create_database_for_chats(db_name)
    async with async_session() as session:
        user = await session.scalar(select(User_chat).where(User_chat.tg_id == int(data["tg_id"])))
        if not user:
            session.add(User_chat(**data))
        else:
            user.chat_id=int(data["chat_id"])
            if not data["topic_id"] is None:
                user.topic_id=int(data["topic_id"])
        await session.commit()

async def get_user_tg_id(tg_id: int):
    """
    получение данный о пользователе по tg_id
    """
    logging.info('get_user_tg_id')
    async_session = await create_database_for_chats(db_name=FolderName.users)
    async with async_session() as session:
        user = await session.scalar(select(User_chat).where(User_chat.tg_id == tg_id))
        if not user:
            return False
        else:
            return user

async def get_user_other_data(chat_id: int, topic_id: int):
    """
       получение данный о пользователе по chat_id и topic_id
       """
    logging.info('get_user_tg_id')
    async_session = await create_database_for_chats(db_name=FolderName.users)
    async with async_session() as session:
        user = await session.scalar(select(User_chat).where(User_chat.chat_id==chat_id and User_chat.topic_id==topic_id))
        if not user: return False
        else: return user
