import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .create import Estate

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

DATABASE_URL = "postgresql+asyncpg://admin:password@localhost/estate"

# Создание асинхронного двигателя и фабрики сессий
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_last_msg_id(group_id: str) -> int:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(func.max(Estate.msg_id)).where(Estate.group_id == group_id)
            )
            last_msg_id = result.scalar_one_or_none()
            return last_msg_id if last_msg_id is not None else 0


async def insert_estates_web(estates: list) -> None:
    async with async_session() as session:
        async with session.begin():
            for estate in estates:
                new_estate = Estate(
                    datetime=func.now(),
                    city=estate['city'],
                    resource=estate['resource'],
                    district=estate.get('district', ''),
                    rooms=estate.get('rooms', -1),
                    price=estate['price'],
                    url=estate.get('url', ''),
                    group_id=estate.get('group_id', -1),
                    msg_id=estate.get('msg_id', -1),
                    language=estate.get('language', ''),
                    msg=estate['msg'],
                    msg_ru=estate.get('msg_ru', ''),
                    msg_en=estate.get('msg_en', ''),
                    msg_el=estate.get('msg_el', '')
                )
                session.add(new_estate)
        await session.commit()
