from time import sleep

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import Post
from tests.conftest import async_session_maker


async def test_user_read_comments(register_and_login_user, ac: AsyncClient):
    post_id = 1
    response = await ac.get(f"/posts/{post_id}/comments/", cookies=register_and_login_user)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1  # Ensure that user can`t see blocked posts


async def test_admin_read_comments(create_and_login_admin, ac: AsyncClient):
    post_id = 1
    response = await ac.get(f"/posts/{post_id}/comments/", cookies=create_and_login_admin)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2  # Ensure that admin can see all comments


async def test_read_comments_pagination(create_and_login_admin, ac: AsyncClient):
    post_id = 1
    params = {"offset": 0, "limit": 5}
    response = await ac.get(f"/posts/{post_id}/comments/", params=params, cookies=create_and_login_admin)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.parametrize("sort_by, sort_order", [
    ("created_at", "asc"),
    ("created_at", "desc"),
    ("author_id", "asc"),
    ("author_id", "desc"),
])
async def test_read_comments_sorting(create_and_login_admin, ac: AsyncClient, sort_by, sort_order):
    post_id = 1
    params = {"sort_by": sort_by, "sort_order": sort_order}
    response = await ac.get(f"/posts/{post_id}/comments/", params=params, cookies=create_and_login_admin)
    assert response.status_code == 200
    data = response.json()

    if sort_by == "author_id":
        sorted_data = sorted(data, key=lambda x: x["author_id"], reverse=(sort_order == "desc"))
    else:
        sorted_data = sorted(data, key=lambda x: x["created_at"], reverse=(sort_order == "desc"))
    assert data == sorted_data, f"Comments should be sorted by {sort_by} in {sort_order} order"


async def test_read_comments_unauthenticated(ac: AsyncClient):
    post_id = 1

    response = await ac.get(f"/posts/{post_id}/comments/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


async def test_user_read_comment(register_and_login_user, ac: AsyncClient):
    comment_id = 1
    response = await ac.get(f"/comments/{comment_id}/", cookies=register_and_login_user)

    assert response.status_code == 200, f"Failed to read comment {comment_id}: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["id"] == comment_id


async def test_user_can_not_read_blocked_post(register_and_login_user, ac: AsyncClient):
    # Test blocked comment reading
    comment_id = 2
    response = await ac.get(f"/comments/{comment_id}/", cookies=register_and_login_user)

    assert response.status_code == 403, f"Failed to read blocked comment by user {comment_id}: {response.content}"
    assert response.json()["detail"] == "Comment is blocked"


async def test_admin_can_read_blocked_post(create_and_login_admin, ac: AsyncClient):
    # Test blocked comment reading by admin
    comment_id = 6
    response = await ac.get(f"/comments/{comment_id}/", cookies=create_and_login_admin)

    assert response.status_code == 200, f"Failed to read blocked comment by admin {comment_id}: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["id"] == comment_id  # Ensure that admin can see blocked comment


async def test_create_comment(register_and_login_user, ac: AsyncClient):
    post_id = 1
    content = "This is a user test comment"

    response = await ac.post(
        f"/posts/{post_id}/comments/",
        cookies=register_and_login_user,
        json={"post_id": post_id, "content": content}
    )

    assert response.status_code == 201, f"Failed to create comment: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["post_id"] == post_id
    assert response.json()["content"] == content


async def test_update_comment(register_and_login_user, ac: AsyncClient):
    comment_id = 1
    content = "This is an updated user test comment"

    response = await ac.put(
        f"/comments/{comment_id}/",
        cookies=register_and_login_user,
        json={"content": content}
    )

    assert response.status_code == 200, f"Failed to update comment {comment_id}: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["id"] == comment_id
    assert response.json()["content"] == content

async def test_delete_comment(register_and_login_user, ac: AsyncClient):
    comment_id = 1

    response = await ac.delete(f"/comments/{comment_id}/", cookies=register_and_login_user)

    assert response.status_code == 204, f"Failed to delete comment {comment_id}: {response.content}"


async def test_comment_moderation(register_and_login_user, ac: AsyncClient):
    post_id = 1
    content = "Fuck this shit, I`m out"

    response = await ac.post(
        f"/posts/{post_id}/comments/",
        cookies=register_and_login_user,
        json={"content": content}
    )

    assert response.status_code == 201, f"Failed to create post: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["content"] == content
    assert response.json()["is_blocked"] == True  # Ensure that comment is blocked after moderation


# This test could not work if you don`t have access to Gemini
async def test_comment_with_hate(register_and_login_user, ac: AsyncClient):
    post_id = 1
    content = "I hate Jews and gypsies"

    response = await ac.post(
        f"/posts/{post_id}/comments/",
        cookies=register_and_login_user,
        json={"content": content}
    )

    assert response.status_code == 201, f"Failed to create post: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["content"] == content
    assert response.json()["is_blocked"] == True, "Hateful comment could not be blocked, if you don`t have access to Gemini"

async def test_auto_reply(register_and_login_user, ac: AsyncClient):
    async with async_session_maker() as session:
        result = await session.execute(select(Post).where(Post.id == 1))
        post = result.scalar_one_or_none()

        if post:
            post.auto_reply = True

            await session.commit()
            await session.refresh(post)

    post_id = 1
    content = "This is a user test comment"

    response = await ac.post(
        f"/posts/{post_id}/comments/",
        cookies=register_and_login_user,
        json={"post_id": post_id, "content": content}
    )
    comment_id = response.json()["id"]

    assert response.status_code == 201, f"Failed to create comment: {response.content}"

    sleep(3)

    response = await ac.get(
        f"/posts/{post_id}/comments/",
        cookies=register_and_login_user,
    )
    comments = response.json()
    reply = comments[-1]
    assert reply["parent_id"] == comment_id
    assert len(reply["content"]) >= 0
