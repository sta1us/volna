"""
Тесты: /api/media/
"""

import io
from datetime import datetime, timedelta, timezone

import pytest
from common.models import Event, Media, MediaType
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Фабрики
# ---------------------------------------------------------------------------


async def create_event(db: AsyncSession) -> Event:
    event = Event(
        title="Событие для медиа",
        description="Описание события для тестирования медиа",
        date_time=(datetime.now(timezone.utc) + timedelta(days=5)).replace(tzinfo=None),
        image_path="uploads/events/test.jpg",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def create_media(
    db: AsyncSession,
    file_path: str = "uploads/media/test.jpg",
    media_type: MediaType = MediaType.IMAGE,
    event_id: int | None = None,
) -> Media:
    m = Media(
        file_path=file_path,
        media_type=media_type,
        event_id=event_id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


def fake_image(name: str = "photo.jpg") -> tuple:
    return (name, io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 50), "image/jpeg")


def fake_video(name: str = "clip.mp4") -> tuple:
    return (name, io.BytesIO(b"\x00\x00\x00\x18ftyp" + b"\x00" * 50), "video/mp4")


def fake_unsupported(name: str = "doc.pdf") -> tuple:
    return (name, io.BytesIO(b"%PDF"), "application/pdf")


# ===========================================================================
# GET /api/media/gallery  (публичный)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_gallery_empty(client: AsyncClient):
    """Общая галерея пуста, если медиа нет."""
    response = await client.get("/api/media/gallery")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_gallery_returns_only_non_event_media(
    client: AsyncClient, db_session: AsyncSession
):
    """Общая галерея не содержит медиа, привязанных к событиям."""
    event = await create_event(db_session)
    await create_media(db_session, "uploads/media/general.jpg", event_id=None)
    await create_media(db_session, "uploads/media/event.jpg", event_id=event.id)

    response = await client.get("/api/media/gallery")
    assert response.status_code == 200
    results = response.json()
    assert any(m["file_path"] == "uploads/media/general.jpg" for m in results)
    assert all(m["event_id"] is None for m in results)


@pytest.mark.asyncio
async def test_get_gallery_no_auth_required(client: AsyncClient):
    """Галерея доступна без авторизации."""
    response = await client.get("/api/media/gallery")
    assert response.status_code == 200


# ===========================================================================
# GET /api/media/{event_id}  (публичный)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_event_gallery_empty(client: AsyncClient, db_session: AsyncSession):
    """Галерея события пуста, если медиа не загружались."""
    event = await create_event(db_session)
    response = await client.get(f"/api/media/{event.id}")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_event_gallery_returns_correct_media(
    client: AsyncClient, db_session: AsyncSession
):
    """Возвращаются только медиа конкретного события."""
    event = await create_event(db_session)
    await create_media(db_session, "uploads/media/ev1.jpg", event_id=event.id)
    await create_media(db_session, "uploads/media/general2.jpg", event_id=None)

    response = await client.get(f"/api/media/{event.id}")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert all(m["event_id"] == event.id for m in results)


@pytest.mark.asyncio
async def test_get_event_gallery_no_auth_required(
    client: AsyncClient, db_session: AsyncSession
):
    """Галерея события доступна без авторизации."""
    event = await create_event(db_session)
    response = await client.get(f"/api/media/{event.id}")
    assert response.status_code == 200


# ===========================================================================
# POST /api/media/upload-multiple  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_upload_multiple_images_as_admin(client: AsyncClient, admin_token: str):
    """Администратор загружает несколько изображений в общую галерею."""
    response = await client.post(
        "/api/media/upload-multiple",
        headers=auth_headers(admin_token),
        files=[
            ("files", fake_image("photo1.jpg")),
            ("files", fake_image("photo2.jpg")),
        ],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert len(body["uploaded"]) == 2
    assert all(r["status"] == "success" for r in body["uploaded"])


@pytest.mark.asyncio
async def test_upload_media_to_event_gallery(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Загрузка медиа с привязкой к событию."""
    event = await create_event(db_session)
    response = await client.post(
        "/api/media/upload-multiple",
        headers=auth_headers(admin_token),
        data={"event_id": str(event.id)},
        files=[("files", fake_image("event_photo.jpg"))],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["uploaded"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_upload_media_with_caption(client: AsyncClient, admin_token: str):
    """Загрузка медиа с текстовой подписью."""
    response = await client.post(
        "/api/media/upload-multiple",
        headers=auth_headers(admin_token),
        data={"caption": "Летняя веранда"},
        files=[("files", fake_image("verandah.jpg"))],
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_unsupported_format_skipped(client: AsyncClient, admin_token: str):
    """Файл неподдерживаемого формата пропускается (status='skipped...')."""
    response = await client.post(
        "/api/media/upload-multiple",
        headers=auth_headers(admin_token),
        files=[("files", fake_unsupported())],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["uploaded"][0]["status"].startswith("skipped")


@pytest.mark.asyncio
async def test_upload_mixed_supported_and_unsupported(
    client: AsyncClient, admin_token: str
):
    """Смешанная загрузка: поддерживаемый файл — success, неподдерживаемый — skipped."""
    response = await client.post(
        "/api/media/upload-multiple",
        headers=auth_headers(admin_token),
        files=[
            ("files", fake_image("valid.jpg")),
            ("files", fake_unsupported("bad.exe")),
        ],
    )
    assert response.status_code == 201
    results = response.json()["uploaded"]
    statuses = {r["filename"]: r["status"] for r in results}
    assert statuses["valid.jpg"] == "success"
    assert statuses["bad.exe"].startswith("skipped")


@pytest.mark.asyncio
async def test_upload_media_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может загружать медиа."""
    response = await client.post(
        "/api/media/upload-multiple",
        headers=auth_headers(client_token),
        files=[("files", fake_image())],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_media_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.post(
        "/api/media/upload-multiple",
        files=[("files", fake_image())],
    )
    assert response.status_code == 401


# ===========================================================================
# DELETE /api/media/delete-multiple  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_multiple_media_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор удаляет несколько медиафайлов по ID."""
    m1 = await create_media(db_session, "uploads/media/del1.jpg")
    m2 = await create_media(db_session, "uploads/media/del2.jpg")

    response = await client.request(
        "DELETE",
        "/api/media/delete-multiple",
        headers=auth_headers(admin_token),
        json=[m1.id, m2.id],
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "2" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_multiple_media_not_found(client: AsyncClient, admin_token: str):
    """Если ни один ID не найден → 404."""
    response = await client.request(
        "DELETE",
        "/api/media/delete-multiple",
        headers=auth_headers(admin_token),
        json=[999991, 999992],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_multiple_media_partial(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Удаляются только существующие ID; несуществующие молча игнорируются."""
    m = await create_media(db_session, "uploads/media/partial.jpg")

    response = await client.request(
        "DELETE",
        "/api/media/delete-multiple",
        headers=auth_headers(admin_token),
        json=[m.id, 999993],
    )
    assert response.status_code == 200
    assert "1" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_multiple_media_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может удалять медиа."""
    m = await create_media(db_session, "uploads/media/forbidden.jpg")
    response = await client.request(
        "DELETE",
        "/api/media/delete-multiple",
        headers=auth_headers(client_token),
        json=[m.id],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_multiple_media_no_auth(
    client: AsyncClient, db_session: AsyncSession
):
    """Без токена → 401."""
    m = await create_media(db_session, "uploads/media/noauth.jpg")
    response = await client.request(
        "DELETE",
        "/api/media/delete-multiple",
        json=[m.id],
    )
    assert response.status_code == 401
