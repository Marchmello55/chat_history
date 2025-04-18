from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import os


class Base(AsyncAttrs, DeclarativeBase):
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


async def create_database(db_name: str):
    os.makedirs("database", exist_ok=True)
    db_path = f"sqlite+aiosqlite:///database/{db_name}.sqlite3"
    engine = create_async_engine(db_path, echo=False)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Возвращаем фабрику сессий
    return async_sessionmaker(engine, expire_on_commit=False)

