from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, \
    async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import DATABASE_URL

load_dotenv()

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


from app.models import User


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_db() -> AsyncSession:
    """Create a new database session for each request."""
    db = async_session_maker()
    try:
        yield db
    finally:
        await db.close()
