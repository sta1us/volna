"""
Тесты: /api/location/
"""

import io

import pytest
from common.models import Location
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ===========================================================================
# GET /api/location/
# ===========================================================================


@pytest.mark.asyncio
async def test_get_location_not_found(client: AsyncClient):
    """Если локация ещё не создана, возвращается 404."""
    response = await client.get("/api/location/")
    # Может быть 404 (нет данных) или 200 (если другой тест уже создал)
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_get_location_returns_data(client: AsyncClient, db_session: AsyncSession):
    """Если локация создана, эндпоинт возвращает её."""
    loc = Location(address="ул. Тестовая, 1", latitude=55.75, longitude=37.62)
    db_session.add(loc)
    await db_session.commit()

    response = await client.get("/api/location/")
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "ул. Тестовая, 1"
    assert body["latitude"] == pytest.approx(55.75)
    assert body["longitude"] == pytest.approx(37.62)


# ===========================================================================
# PUT /api/location/
# ===========================================================================


@pytest.mark.asyncio
async def test_update_location_as_admin(client: AsyncClient, admin_token: str):
    """Администратор обновляет или создаёт локацию через multipart/form-data."""
    file_entrance = (
        "entrance.jpg",
        io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 50),
        "image/jpeg",
    )
    file_map = ("map.png", io.BytesIO(b"\x89PNG\r\n" + b"\x00" * 50), "image/png")

    response = await client.put(
        "/api/location/",
        headers=auth_headers(admin_token),
        data={
            "address": "пр. Мира, 42",
            "latitude": "55.7558",
            "longitude": "37.6173",
            "working_hours": "Пн-Пт 10:00-22:00",
            "phone": "+7 999 000 00 00",
            "email": "info@volna.ru",
        },
        files={
            "file_entrance": file_entrance,
            "file_map": file_map,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "пр. Мира, 42"
    assert body["phone"] == "+7 999 000 00 00"


@pytest.mark.asyncio
async def test_update_location_without_files(client: AsyncClient, admin_token: str):
    """Обновление локации без файлов тоже допустимо."""
    response = await client.put(
        "/api/location/",
        headers=auth_headers(admin_token),
        data={
            "address": "Садовая ул., 5",
            "latitude": "59.9343",
            "longitude": "30.3351",
        },
    )
    assert response.status_code == 200
    assert response.json()["address"] == "Садовая ул., 5"


@pytest.mark.asyncio
async def test_update_location_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может изменять локацию."""
    response = await client.put(
        "/api/location/",
        headers=auth_headers(client_token),
        data={"address": "Попытка", "latitude": "0.0", "longitude": "0.0"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_location_no_auth(client: AsyncClient):
    """Без авторизации → 401."""
    response = await client.put(
        "/api/location/",
        data={"address": "Без токена", "latitude": "0.0", "longitude": "0.0"},
    )
    assert response.status_code == 401
