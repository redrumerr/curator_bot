from global_variables.token import SQLALCHEMY_DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import select, insert, update, delete, and_, create_engine, desc, asc


engine = create_async_engine(url=SQLALCHEMY_DATABASE_URL)
Async_Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
async_session = Async_Session()


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
