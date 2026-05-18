"""
Тесты: /api/suggestions/
"""

import pytest
from common.models import Suggestion, SuggestionStatus
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Фабрика предложения
# ---------------------------------------------------------------------------


async def create_suggestion(
    db: AsyncSession,
    text: str = "Добавьте больше вегетарианских блюд в меню заведения",
    status: SuggestionStatus = SuggestionStatus.PENDING,
    is_read: bool = False,
) -> Suggestion:
    s = Suggestion(
        guest_name="Тестовый гость",
        guest_contact="+7 999 000 00 00",
        subject="Тест",
        text=text,
        is_read=is_read,
        status=status,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


# ===========================================================================
# POST /api/suggestions/
# ===========================================================================


@pytest.mark.asyncio
async def test_create_suggestion_as_guest(client: AsyncClient):
    """Гость создаёт предложение, передавая guest_name и guest_contact."""
    response = await client.post(
        "/api/suggestions/",
        json={
            "text": "Сделайте детское меню, пожалуйста",
            "subject": "Предложение по меню",
            "guest_name": "Ольга",
            "guest_contact": "+7 900 000 00 00",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"


@pytest.mark.asyncio
async def test_create_suggestion_as_authorized_user(
    client: AsyncClient, client_token: str
):
    """Авторизованный пользователь не обязан передавать guest_name/guest_contact."""
    response = await client.post(
        "/api/suggestions/",
        headers=auth_headers(client_token),
        json={
            "text": "Хотелось бы видеть живую музыку по пятницам",
            "subject": "Живая музыка",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_create_suggestion_guest_missing_name(client: AsyncClient):
    """Гость без guest_name получает 400."""
    response = await client.post(
        "/api/suggestions/",
        json={
            "text": "Добавьте новый сорт пива в меню бара заведения",
            "guest_contact": "+7 999 999 99 99",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_suggestion_guest_missing_contact(client: AsyncClient):
    """Гость без guest_contact получает 400."""
    response = await client.post(
        "/api/suggestions/",
        json={
            "text": "Хотелось бы добавить завтраки в меню заведения",
            "guest_name": "Анна",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_suggestion_text_too_short(client: AsyncClient):
    """Текст меньше 10 символов → 422."""
    response = await client.post(
        "/api/suggestions/",
        json={
            "text": "Кратко",
            "guest_name": "Иван",
            "guest_contact": "+7 999 000 00 00",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_suggestion_empty_name_whitespace(client: AsyncClient):
    """guest_name из пробелов → 400 (защита от пустых строк)."""
    response = await client.post(
        "/api/suggestions/",
        json={
            "text": "Предложение с пустым именем и контактом",
            "guest_name": "   ",
            "guest_contact": "+7 999 000 00 00",
        },
    )
    assert response.status_code == 400


# ===========================================================================
# GET /api/suggestions/  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_suggestions_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор получает полный список предложений."""
    await create_suggestion(db_session, "Первое тестовое предложение для списка")
    await create_suggestion(db_session, "Второе тестовое предложение для списка")

    response = await client.get("/api/suggestions/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_suggestions_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может просматривать предложения."""
    response = await client.get("/api/suggestions/", headers=auth_headers(client_token))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_suggestions_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/suggestions/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_suggestions_filter_by_is_read(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Фильтр is_read=false возвращает только непрочитанные."""
    await create_suggestion(
        db_session, "Непрочитанное предложение для фильтра", is_read=False
    )
    await create_suggestion(
        db_session, "Прочитанное предложение для фильтра", is_read=True
    )

    response = await client.get(
        "/api/suggestions/?is_read=false", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    results = response.json()
    assert all(r["is_read"] is False for r in results)


@pytest.mark.asyncio
async def test_get_suggestions_filter_by_status(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Фильтр status=pending возвращает только ожидающие обработки."""
    await create_suggestion(
        db_session,
        "Pending предложение для фильтра по статусу",
        status=SuggestionStatus.PENDING,
    )
    await create_suggestion(
        db_session,
        "Planned предложение для фильтра по статусу",
        status=SuggestionStatus.PLANNED,
    )

    response = await client.get(
        "/api/suggestions/?status=pending", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    results = response.json()
    assert all(r["status"] == SuggestionStatus.PENDING.value for r in results)


# ===========================================================================
# PATCH /api/suggestions/{id}/read
# ===========================================================================


@pytest.mark.asyncio
async def test_mark_suggestion_read(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор помечает предложение как прочитанное."""
    s = await create_suggestion(db_session, "Пометить как прочитанное предложение")
    response = await client.patch(
        f"/api/suggestions/{s.id}/read", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_mark_suggestion_read_not_found(client: AsyncClient, admin_token: str):
    """Несуществующее предложение → 404."""
    response = await client.patch(
        "/api/suggestions/999999/read", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_suggestion_read_forbidden(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может помечать предложения."""
    s = await create_suggestion(db_session, "Попытка клиента пометить предложение")
    response = await client.patch(
        f"/api/suggestions/{s.id}/read", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


# ===========================================================================
# PATCH /api/suggestions/{id}/status
# ===========================================================================


@pytest.mark.asyncio
async def test_change_suggestion_status_planned(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор переводит предложение в статус 'planned'."""
    s = await create_suggestion(db_session, "Предложение для смены статуса на planned")
    response = await client.patch(
        f"/api/suggestions/{s.id}/status",
        headers=auth_headers(admin_token),
        json={"status": "planned"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_change_suggestion_status_rejected(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор переводит предложение в статус 'rejected'."""
    s = await create_suggestion(db_session, "Предложение для отклонения в тесте")
    response = await client.patch(
        f"/api/suggestions/{s.id}/status",
        headers=auth_headers(admin_token),
        json={"status": "rejected"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_suggestion_status_invalid(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Невалидный статус → 422."""
    s = await create_suggestion(db_session, "Предложение для невалидного статуса теста")
    response = await client.patch(
        f"/api/suggestions/{s.id}/status",
        headers=auth_headers(admin_token),
        json={"status": "flying_unicorn"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_suggestion_status_not_found(
    client: AsyncClient, admin_token: str
):
    """Несуществующее предложение → 404."""
    response = await client.patch(
        "/api/suggestions/999999/status",
        headers=auth_headers(admin_token),
        json={"status": "planned"},
    )
    assert response.status_code == 404


# ===========================================================================
# DELETE /api/suggestions/{id}
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_suggestion_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор удаляет предложение."""
    s = await create_suggestion(db_session, "Предложение которое будет удалено тестом")
    response = await client.delete(
        f"/api/suggestions/{s.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_delete_suggestion_not_found(client: AsyncClient, admin_token: str):
    """Удаление несуществующего предложения → 404."""
    response = await client.delete(
        "/api/suggestions/999999", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_suggestion_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может удалять предложения."""
    s = await create_suggestion(
        db_session, "Предложение которое клиент пытается удалить"
    )
    response = await client.delete(
        f"/api/suggestions/{s.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403
