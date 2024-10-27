import asyncio
import os
from typing import AsyncGenerator
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.main import app
from app.models import User, Post, Comment, Base


# Init the test database

engine_test = create_async_engine(TEST_DATABASE_URL, echo=True, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)
Base.metadata.bind = engine_test


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the event loop for the tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

user_email = "testuser@example.com"
user_password = "string"


@pytest.fixture(scope="session")
async def register_and_login_user(ac: AsyncClient):
    email = "testuser@example.com"
    password = "string"
    # User registration
    registration_url = "/auth/register"
    registration_data = {
        "email": email,
        "password": password,
        "is_active": True,
        "is_superuser": True,
        "is_verified": True,
    }

    registration_response = await ac.post(registration_url, json=registration_data)
    assert registration_response.status_code == 201, f"Failed to register user: {registration_response}"
    assert registration_response.json()["email"] == "testuser@example.com"
    assert registration_response.json()["is_superuser"] == False #fastapi_users should ignore is_superuser in registration
    assert registration_response.json()["is_verified"] == False  #fastapi_users should ignore is_verified in registration

    # User login
    login_url = "/auth/jwt/login"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    login_data = {
        "username": email,
        "password": password,
    }
    form_data = urlencode(login_data)

    login_response = await ac.post(login_url, headers=headers, content=form_data)
    assert login_response.status_code == 204, f"Failed to log in user: {login_response.content}"

    cookies = login_response.cookies
    return {"blog": cookies.get("blog")}


@pytest.fixture(scope="session")
async def create_and_login_admin(ac: AsyncClient):
    email = "test_admin@example.com"
    password = "string"

    registration_url = "/auth/register"
    registration_data = {
        "email": email,
        "password": password,
    }

    registration_response = await ac.post(registration_url, json=registration_data)
    assert registration_response.status_code == 201, f"Failed to register user: {registration_response}"


    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.is_superuser = True

            await session.commit()
            await session.refresh(user)


    # Admin login
    login_url = "/auth/jwt/login"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    login_data = {
        "username": email,
        "password": password,
    }
    form_data = urlencode(login_data)

    login_response = await ac.post(login_url, headers=headers,
                                   content=form_data)
    assert login_response.status_code == 204, f"Failed to log in admin: {login_response.content}"

    cookies = login_response.cookies
    return {"blog": cookies.get("blog")}


@pytest.fixture(scope="session")
async def create_test_data(ac: AsyncClient):
    async with async_session_maker() as session:
        # Create 5 usual posts
        for i in range(5):
            post = Post(
                title=f"Test Post {i}",
                content="This is a test post.",
                owner_id=1,
            )
            session.add(post)

        await session.commit()
        # Create 5 blocked posts
        for i in range(5, 10):
            post = Post(
                title=f"Test Post {i}",
                content="This is a blocked post.",
                owner_id=1,
                is_blocked=True,
            )
            session.add(post)

        await session.commit()

        # Create 1 normal comment and 1 blocked comment for each post
        posts = await session.execute(select(Post))
        posts = posts.scalars().all()

        for post in posts:
            comment = Comment(
                post_id=post.id,
                content=f"Test Comment for Post {post.id}",
                author_id=1,
            )
            blocked_comment = Comment(
                post_id=post.id,
                content=f"Test Blocked Comment for Post {post.id}",
                author_id=1,
                is_blocked=True,
             )
            session.add(comment)
            session.add(blocked_comment)

        await session.commit()

@pytest.fixture(autouse=True)
async def setup_test_data(create_test_data):
    pass
