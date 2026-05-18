"""
Тесты: /api/events/
"""

import io
from datetime import datetime, timedelta, timezone

import pytest
from common.models import Event
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Вспомогательная фабрика события
# ---------------------------------------------------------------------------


async def create_event(
    db: AsyncSession, title: str = "Тест ивент", future: bool = True
) -> Event:
    dt = datetime.now(timezone.utc) + timedelta(days=5 if future else -5)
    event = Event(
        title=title,
        description="Описание тестового мероприятия",
        date_time=dt.replace(tzinfo=None),
        image_path="uploads/events/test.jpg",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


def fake_image_file() -> tuple:
    """Возвращает (filename, file-like, content_type) для multipart-запроса."""
    return ("test.jpg", io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100), "image/jpeg")


# ===========================================================================
# GET /api/events/
# ===========================================================================


@pytest.mark.asyncio
async def test_get_events_empty(client: AsyncClient):
    """Пустой список, если мероприятий нет."""
    response = await client.get("/api/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_events_returns_future_only(
    client: AsyncClient, db_session: AsyncSession
):
    """По умолчанию upcoming_only=True — прошедшие события не возвращаются."""
    await create_event(db_session, "Будущее событие", future=True)
    await create_event(db_session, "Прошедшее событие", future=False)

    response = await client.get("/api/events/")
    assert response.status_code == 200
    titles = [e["title"] for e in response.json()]
    assert "Будущее событие" in titles
    assert "Прошедшее событие" not in titles


@pytest.mark.asyncio
async def test_get_events_all_when_upcoming_false(
    client: AsyncClient, db_session: AsyncSession
):
    """upcoming_only=false возвращает все события, включая прошедшие."""
    await create_event(db_session, "Прошедшее 2", future=False)

    response = await client.get("/api/events/?upcoming_only=false")
    assert response.status_code == 200
    titles = [e["title"] for e in response.json()]
    assert "Прошедшее 2" in titles


# ===========================================================================
# GET /api/events/{event_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_get_event_by_id(client: AsyncClient, db_session: AsyncSession):
    """Существующее событие возвращается по ID."""
    event = await create_event(db_session, "Детальный ивент")
    response = await client.get(f"/api/events/{event.id}")
    assert response.status_code == 200
    assert response.json()["id"] == event.id
    assert response.json()["title"] == "Детальный ивент"


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient):
    """Несуществующий ID → 404."""
    response = await client.get("/api/events/999999")
    assert response.status_code == 404


# ===========================================================================
# GET /api/events/{event_id}/stats
# ===========================================================================


@pytest.mark.asyncio
async def test_get_event_stats_empty(client: AsyncClient, db_session: AsyncSession):
    """Статистика для нового события: total=0, going=0, maybe=0."""
    event = await create_event(db_session, "Ивент для статы")
    response = await client.get(f"/api/events/{event.id}/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["going"] == 0
    assert body["maybe"] == 0


# ===========================================================================
# POST /api/events/ (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_create_event_as_admin(client: AsyncClient, admin_token: str):
    """Администратор создаёт событие через form-data + файл."""
    fname, fdata, ftype = fake_image_file()
    response = await client.post(
        "/api/events/",
        headers=auth_headers(admin_token),
        data={
            "title": "Новый концерт",
            "description": "Описание нового концерта длиннее 10 символов",
            "date_time": "2030-06-15T20:00:00",
        },
        files={"file": (fname, fdata, ftype)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Новый концерт"
    assert "image_url" in body


@pytest.mark.asyncio
async def test_create_event_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может создавать события."""
    fname, fdata, ftype = fake_image_file()
    response = await client.post(
        "/api/events/",
        headers=auth_headers(client_token),
        data={
            "title": "Попытка клиента",
            "description": "Описание попытки клиента создать ивент",
            "date_time": "2030-06-15T20:00:00",
        },
        files={"file": (fname, fdata, ftype)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_event_no_auth(client: AsyncClient):
    """Без токена → 401."""
    fname, fdata, ftype = fake_image_file()
    response = await client.post(
        "/api/events/",
        data={
            "title": "Без токена",
            "description": "Описание без токена авторизации",
            "date_time": "2030-06-15T20:00:00",
        },
        files={"file": (fname, fdata, ftype)},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_event_short_title_validation(
    client: AsyncClient, admin_token: str
):
    """Слишком короткий title (< 3 символов) → 422."""
    fname, fdata, ftype = fake_image_file()
    response = await client.post(
        "/api/events/",
        headers=auth_headers(admin_token),
        data={
            "title": "аб",
            "description": "Описание с нормальной длиной для теста",
            "date_time": "2030-06-15T20:00:00",
        },
        files={"file": (fname, fdata, ftype)},
    )
    assert response.status_code == 422


# ===========================================================================
# POST /api/events/{event_id}/react
# ===========================================================================


@pytest.mark.asyncio
async def test_react_to_event_going(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Авторизованный пользователь может поставить реакцию 'going'."""
    event = await create_event(db_session, "Ивент с реакцией")
    response = await client.post(
        f"/api/events/{event.id}/react",
        headers=auth_headers(client_token),
        json={"status": "going"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "going"


@pytest.mark.asyncio
async def test_react_to_event_update(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Повторная реакция обновляет статус."""
    event = await create_event(db_session, "Ивент смена реакции")
    await client.post(
        f"/api/events/{event.id}/react",
        headers=auth_headers(client_token),
        json={"status": "going"},
    )
    response = await client.post(
        f"/api/events/{event.id}/react",
        headers=auth_headers(client_token),
        json={"status": "maybe"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "maybe"


@pytest.mark.asyncio
async def test_react_to_nonexistent_event(client: AsyncClient, client_token: str):
    """Реакция на несуществующее событие → 404."""
    response = await client.post(
        "/api/events/999999/react",
        headers=auth_headers(client_token),
        json={"status": "going"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_react_no_auth(client: AsyncClient, db_session: AsyncSession):
    """Реакция без токена → 401."""
    event = await create_event(db_session, "Ивент без авторизации")
    response = await client.post(
        f"/api/events/{event.id}/react",
        json={"status": "going"},
    )
    assert response.status_code == 401


# ===========================================================================
# PUT /api/events/{event_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_update_event_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор может обновить событие."""
    event = await create_event(db_session, "Оригинальное название")
    fname, fdata, ftype = fake_image_file()
    response = await client.put(
        f"/api/events/{event.id}",
        headers=auth_headers(admin_token),
        data={
            "title": "Обновлённое название",
            "description": "Обновлённое описание мероприятия для теста",
            "date_time": "2030-07-01T18:00:00",
        },
        files={"file": (fname, fdata, ftype)},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Обновлённое название"


@pytest.mark.asyncio
async def test_update_event_not_found(client: AsyncClient, admin_token: str):
    """Обновление несуществующего события → 404."""
    fname, fdata, ftype = fake_image_file()
    response = await client.put(
        "/api/events/999999",
        headers=auth_headers(admin_token),
        data={"title": "Без смысла"},
        files={"file": (fname, fdata, ftype)},
    )
    assert response.status_code == 404


# ===========================================================================
# DELETE /api/events/{event_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_event_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор удаляет событие."""
    event = await create_event(db_session, "На удаление")
    response = await client.delete(
        f"/api/events/{event.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Проверяем, что события больше нет
    get_response = await client.get(f"/api/events/{event.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может удалять события."""
    event = await create_event(db_session, "Нельзя удалить клиенту")
    response = await client.delete(
        f"/api/events/{event.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_event_not_found(client: AsyncClient, admin_token: str):
    """Удаление несуществующего события → 404."""
    response = await client.delete(
        "/api/events/999999", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404
