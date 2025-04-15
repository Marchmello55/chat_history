from database.models import create_database
from database.models import User
import logging

async def add_user(db_name: str, data: dict) -> None:
    logging.info(f'add_user')
    async_session = await create_database(db_name)
    async with async_session() as session:
        session.add(User(**data))
        await session.commit()