import pytest

from httpx import AsyncClient


async def test_user_can_not_read_analytics(register_and_login_user, ac: AsyncClient):
    response = await ac.get(f"/comments-daily-breakdown/", cookies=register_and_login_user)
    assert response.status_code == 403, f"Failed to read analytics by user: {response.content}"



async def test_admin_read_analytics(create_and_login_admin, ac: AsyncClient):
    response = await ac.get(f"/comments-daily-breakdown/", cookies=create_and_login_admin)
    analytics = response.json()
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "date" in analytics[0]
    assert "total_comments" in analytics[0]
    assert "blocked_comments" in analytics[0]


async def test_read_analytics_pagination(create_and_login_admin, ac: AsyncClient):
    params = {"offset": 0, "limit": 5}
    response = await ac.get(f"/comments-daily-breakdown/", params=params, cookies=create_and_login_admin)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.parametrize("sort_order", [
    "asc",
    "desc",
])
async def test_read_analytics_sorting(create_and_login_admin, ac: AsyncClient, sort_order):
    params = {"sort_order": sort_order}
    response = await ac.get(f"/comments-daily-breakdown/", params=params, cookies=create_and_login_admin)
    assert response.status_code == 200
    data = response.json()

    sorted_data = sorted(data, key=lambda x: x["date"], reverse=(sort_order == "desc"))

    assert data == sorted_data, f"Analytics should be sorted in {sort_order} order"
