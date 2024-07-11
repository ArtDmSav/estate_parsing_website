from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DateTime, Text, Time, func, UniqueConstraint
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime
from databases import Database

DATABASE_URL = "postgresql+asyncpg://admin:password@localhost/estate"

database = Database(DATABASE_URL)
Base = declarative_base()


class Estate(Base):
    __tablename__ = "estates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource = Column(Integer)
    datetime = Column(DateTime, default=datetime.now)
    city = Column(String(20))
    district = Column(String(20), default='')
    rooms = Column(Integer, default=-1)
    price = Column(Integer)
    url = Column(Text, default='')
    group_id = Column(String(32), default='')
    msg_id = Column(Integer, default=-1)
    msg = Column(Text)
    language = Column(String(4))
    msg_ru = Column(Text)
    msg_en = Column(Text)
    msg_el = Column(Text)


async def create_tables():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_tables())
