"""
Тесты: /api/menu/
"""

import io

import pytest
from common.models import MenuCategory, MenuPage
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Фабрика страницы меню
# ---------------------------------------------------------------------------


async def create_menu_page(
    db: AsyncSession,
    category: MenuCategory = MenuCategory.KITCHEN,
    order_num: int = 0,
) -> MenuPage:
    page = MenuPage(
        category=category,
        image_path="uploads/menu/test.jpg",
        order_num=order_num,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


def fake_image(name: str = "menu.jpg", content_type: str = "image/jpeg") -> tuple:
    return (name, io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 50), content_type)


# ===========================================================================
# GET /api/menu/
# ===========================================================================


@pytest.mark.asyncio
async def test_get_menu_empty(client: AsyncClient):
    """Публичный эндпоинт возвращает пустой список, если страниц нет."""
    response = await client.get("/api/menu/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_menu_all_categories(client: AsyncClient, db_session: AsyncSession):
    """Без фильтра возвращаются страницы всех категорий."""
    await create_menu_page(db_session, MenuCategory.KITCHEN)
    await create_menu_page(db_session, MenuCategory.BAR)

    response = await client.get("/api/menu/")
    assert response.status_code == 200
    categories = {p["category"] for p in response.json()}
    assert MenuCategory.KITCHEN.value in categories
    assert MenuCategory.BAR.value in categories


@pytest.mark.asyncio
async def test_get_menu_filter_kitchen(client: AsyncClient, db_session: AsyncSession):
    """Фильтр по category=kitchen возвращает только кухню."""
    await create_menu_page(db_session, MenuCategory.KITCHEN, order_num=1)
    await create_menu_page(db_session, MenuCategory.BAR, order_num=2)

    response = await client.get("/api/menu/?category=kitchen")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(p["category"] == MenuCategory.KITCHEN.value for p in results)


@pytest.mark.asyncio
async def test_get_menu_filter_bar(client: AsyncClient, db_session: AsyncSession):
    """Фильтр по category=bar возвращает только бар."""
    await create_menu_page(db_session, MenuCategory.BAR, order_num=1)

    response = await client.get("/api/menu/?category=bar")
    assert response.status_code == 200
    assert all(p["category"] == MenuCategory.BAR.value for p in response.json())


@pytest.mark.asyncio
async def test_get_menu_sorted_by_order_num(
    client: AsyncClient, db_session: AsyncSession
):
    """Страницы возвращаются в порядке возрастания order_num."""
    await create_menu_page(db_session, order_num=10)
    await create_menu_page(db_session, order_num=1)
    await create_menu_page(db_session, order_num=5)

    response = await client.get("/api/menu/")
    assert response.status_code == 200
    nums = [p["order_num"] for p in response.json()]
    assert nums == sorted(nums)


@pytest.mark.asyncio
async def test_get_menu_no_auth_required(client: AsyncClient):
    """Публичный доступ — токен не нужен."""
    response = await client.get("/api/menu/")
    assert response.status_code == 200


# ===========================================================================
# POST /api/menu/
# ===========================================================================


@pytest.mark.asyncio
async def test_upload_menu_page_as_admin(client: AsyncClient, admin_token: str):
    """Администратор загружает страницу меню."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(admin_token),
        data={"category": "kitchen", "order_num": "1"},
        files={"file": fake_image()},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == MenuCategory.KITCHEN.value
    assert body["order_num"] == 1
    assert "image_path" in body


@pytest.mark.asyncio
async def test_upload_menu_page_bar_category(client: AsyncClient, admin_token: str):
    """Загрузка страницы категории 'bar'."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(admin_token),
        data={"category": "bar", "order_num": "0"},
        files={"file": fake_image("bar_page.png", "image/png")},
    )
    assert response.status_code == 201
    assert response.json()["category"] == MenuCategory.BAR.value


@pytest.mark.asyncio
async def test_upload_menu_page_invalid_category(client: AsyncClient, admin_token: str):
    """Невалидная категория → 422."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(admin_token),
        data={"category": "drinks", "order_num": "0"},
        files={"file": fake_image()},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_menu_page_non_image_file(client: AsyncClient, admin_token: str):
    """Не-изображение (PDF) → 400."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(admin_token),
        data={"category": "kitchen", "order_num": "0"},
        files={"file": ("menu.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_menu_page_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может загружать страницы меню."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(client_token),
        data={"category": "kitchen", "order_num": "0"},
        files={"file": fake_image()},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_menu_page_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.post(
        "/api/menu/",
        data={"category": "kitchen", "order_num": "0"},
        files={"file": fake_image()},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_menu_page_order_num_default(
    client: AsyncClient, admin_token: str
):
    """Значение order_num по умолчанию равно 0."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(admin_token),
        data={"category": "bar"},
        files={"file": fake_image()},
    )
    assert response.status_code == 201
    assert response.json()["order_num"] == 0


@pytest.mark.asyncio
async def test_upload_menu_page_order_num_out_of_range(
    client: AsyncClient, admin_token: str
):
    """order_num > 10000 → 422."""
    response = await client.post(
        "/api/menu/",
        headers=auth_headers(admin_token),
        data={"category": "kitchen", "order_num": "99999"},
        files={"file": fake_image()},
    )
    assert response.status_code == 422


# ===========================================================================
# DELETE /api/menu/{page_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_menu_page_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор удаляет страницу меню."""
    page = await create_menu_page(db_session)
    response = await client.delete(
        f"/api/menu/{page.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_delete_menu_page_not_found(client: AsyncClient, admin_token: str):
    """Удаление несуществующей страницы → 404."""
    response = await client.delete(
        "/api/menu/999999", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_menu_page_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может удалять страницы меню."""
    page = await create_menu_page(db_session)
    response = await client.delete(
        f"/api/menu/{page.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_menu_page_no_auth(client: AsyncClient, db_session: AsyncSession):
    """Без токена → 401."""
    page = await create_menu_page(db_session)
    response = await client.delete(f"/api/menu/{page.id}")
    assert response.status_code == 401
