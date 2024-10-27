import pytest
from httpx import AsyncClient


async def test_user_read_posts_default_params(register_and_login_user, ac: AsyncClient):
    response = await ac.get("/posts/", cookies=register_and_login_user)

    assert response.status_code == 200, f"Failed to read posts: {response.content}"
    assert isinstance(response.json(), list)
    assert len(response.json()) == 5  # Ensure that user can`t see blocked posts


async def test_admin_read_posts_default_params(create_and_login_admin, ac: AsyncClient):
    response = await ac.get("/posts/", cookies=create_and_login_admin)

    assert response.status_code == 200, f"Failed to read posts: {response.content}"
    assert isinstance(response.json(), list)
    assert len(response.json()) == 10  # Ensure that admin can see blocked posts


async def test_read_posts_pagination(create_and_login_admin, ac: AsyncClient):
    params = {"offset": 0, "limit": 5}
    response = await ac.get("/posts/", params=params, cookies=create_and_login_admin)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.parametrize("sort_by, sort_order", [
    ("title", "asc"),
    ("title", "desc"),
    ("date", "asc"),
    ("date", "desc"),
])
async def test_read_posts_sorting(create_and_login_admin, ac: AsyncClient, sort_by, sort_order):
    params = {"sort_by": sort_by, "sort_order": sort_order}
    response = await ac.get("/posts/", params=params, cookies=create_and_login_admin)
    assert response.status_code == 200
    data = response.json()

    if sort_by == "title":
        sorted_data = sorted(data, key=lambda x: x["title"], reverse=(sort_order == "desc"))
    else:
        sorted_data = sorted(data, key=lambda x: x["created_at"], reverse=(sort_order == "desc"))
    assert data == sorted_data, f"Posts should be sorted by {sort_by} in {sort_order} order"


async def test_read_posts_unauthenticated(ac: AsyncClient):
    # Проверка доступа для неавторизованного пользователя
    response = await ac.get("/posts/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


async def test_user_read_post(register_and_login_user, ac: AsyncClient):
    # Test normal post reading
    post_id = 1
    response = await ac.get(f"/posts/{post_id}", cookies=register_and_login_user)

    assert response.status_code == 200, f"Failed to read post {post_id}: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["id"] == post_id  # Ensure that user can`t see blocked posts


async def test_user_can_not_read_blocked_post(register_and_login_user, ac: AsyncClient):
    # Test blocked post reading
    post_id = 6
    response = await ac.get(f"/posts/{post_id}", cookies=register_and_login_user)

    assert response.status_code == 403, f"Failed to read blocked post {post_id}: {response.content}"
    assert response.json()["detail"] == "Post is blocked"


async def test_admin_can_read_blocked_post(create_and_login_admin, ac: AsyncClient):
    # Test blocked post reading by admin
    post_id = 6
    response = await ac.get(f"/posts/{post_id}", cookies=create_and_login_admin)

    assert response.status_code == 200, f"Failed to read blocked post {post_id}: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["id"] == post_id  # Ensure that admin can see blocked posts


async def test_create_post(register_and_login_user, ac: AsyncClient):
    title = "User Test post"
    content = "This is a user test post"

    response = await ac.post(
        "/posts/",
        cookies=register_and_login_user,
        json={"title": title, "content": content}
    )

    assert response.status_code == 201, f"Failed to create post: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["title"] == title
    assert response.json()["content"] == content


async def test_update_post(register_and_login_user, ac: AsyncClient):
    post_id = 11
    title = "Updated User Test post"
    content = "This is an updated user test post"

    response = await ac.put(
        f"/posts/{post_id}",
        cookies=register_and_login_user,
        json={"title": title, "content": content}
    )

    assert response.status_code == 200, f"Failed to update post {post_id}: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["id"] == post_id
    assert response.json()["title"] == title
    assert response.json()["content"] == content

async def test_delete_post(register_and_login_user, ac: AsyncClient):
    post_id = 11

    response = await ac.delete(f"/posts/{post_id}", cookies=register_and_login_user)

    assert response.status_code == 204, f"Failed to delete post {post_id}: {response.content}"


async def test_post_moderation(register_and_login_user, ac: AsyncClient):
    title = "Fuck this shit, I`m out"
    content = "I want to be banned"

    response = await ac.post(
        "/posts/",
        cookies=register_and_login_user,
        json={"title": title, "content": content}
    )

    assert response.status_code == 201, f"Failed to create post: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["title"] == title
    assert response.json()["content"] == content
    assert response.json()["is_blocked"] == True  # Ensure that post is blocked after moderation


# This test could not work if you don`t have access to Gemini
async def test_post_with_hate(register_and_login_user, ac: AsyncClient):
    title = "This is a hateful post"
    content = "I hate Jews and gypsies"

    response = await ac.post(
        "/posts/",
        cookies=register_and_login_user,
        json={"title": title, "content": content}
    )

    assert response.status_code == 201, f"Failed to create post: {response.content}"
    assert isinstance(response.json(), dict)
    assert response.json()["title"] == title
    assert response.json()["content"] == content
    assert response.json()["is_blocked"] == True, "Hateful post could not be blocked, if you don`t have access to Gemini"
