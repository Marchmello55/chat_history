from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import os


class Base(AsyncAttrs, DeclarativeBase):
    pass

class No_base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id_message: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String, default='')
    avatar: Mapped[str] = mapped_column(String, default='')
    date: Mapped[str] = mapped_column(String, default='')
    text: Mapped[str] = mapped_column(String, default='')
    file: Mapped[str] = mapped_column(String, default='')
    media: Mapped[str] = mapped_column(String, default='')


class User_chat(No_base):
    __tablename__ = "user_chat"

    tg_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer)
    topic_id: Mapped[int] = mapped_column(Integer, nullable=True)

async def create_database(folder_name: str, db_name: str):
    os.makedirs("database", exist_ok=True)
    os.makedirs(f"database/{folder_name}", exist_ok=True)
    db_path = f"sqlite+aiosqlite:///database/{folder_name}/{db_name}.sqlite3"
    engine = create_async_engine(db_path, echo=False)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Возвращаем фабрику сессий
    return async_sessionmaker(engine, expire_on_commit=False)

async def create_database_for_chats(db_name: str):
    os.makedirs("database", exist_ok=True)
    db_path = f"sqlite+aiosqlite:///database/{db_name}.sqlite3"
    engine = create_async_engine(db_path, echo=False)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(No_base.metadata.create_all)

    # Возвращаем фабрику сессий
    return async_sessionmaker(engine, expire_on_commit=False)