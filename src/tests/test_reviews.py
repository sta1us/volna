"""
Тесты: /api/reviews/
"""

import pytest
from common.models import Review, ReviewStatus
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Фабрика отзыва
# ---------------------------------------------------------------------------


async def create_review(
    db: AsyncSession,
    text: str = "Хороший отзыв о заведении",
    rating: int = 5,
    status: ReviewStatus = ReviewStatus.PENDING,
) -> Review:
    r = Review(text=text, rating=rating, status=status)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


# ===========================================================================
# POST /api/reviews/
# ===========================================================================


@pytest.mark.asyncio
async def test_create_review_as_guest(client: AsyncClient):
    """Гость создаёт отзыв — без авторизации, передаёт guest_name."""
    response = await client.post(
        "/api/reviews/",
        json={
            "text": "Отличное заведение, очень понравилось!",
            "rating": 5,
            "guest_name": "Анна",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Отличное заведение, очень понравилось!"
    assert body["rating"] == 5
    assert "id" in body


@pytest.mark.asyncio
async def test_create_review_as_authorized_user(client: AsyncClient, client_token: str):
    """Авторизованный пользователь создаёт отзыв."""
    response = await client.post(
        "/api/reviews/",
        headers=auth_headers(client_token),
        json={"text": "Мне очень понравилась кухня в этом заведении!", "rating": 4},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rating"] == 4
    assert "id" in body


@pytest.mark.asyncio
async def test_create_review_anonymous(client: AsyncClient, client_token: str):
    """Авторизованный пользователь оставляет анонимный отзыв — запрос проходит."""
    response = await client.post(
        "/api/reviews/",
        headers=auth_headers(client_token),
        json={
            "text": "Анонимное мнение о данном заведении.",
            "rating": 3,
            "is_anonymous": True,
        },
    )
    assert response.status_code == 200
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_create_review_guest_no_name(client: AsyncClient):
    """Гость без guest_name всё равно может создать отзыв — имя подставляется как 'Гость'."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Просто отзыв без имени гостя заведения.", "rating": 4},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_review_rating_max(client: AsyncClient):
    """Рейтинг 5 (максимум) принимается."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Максимальный рейтинг пять звёзд заслужен!", "rating": 5},
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 5


@pytest.mark.asyncio
async def test_create_review_rating_min(client: AsyncClient):
    """Рейтинг 1 (минимум) принимается."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Минимальная оценка за плохое обслуживание.", "rating": 1},
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 1


@pytest.mark.asyncio
async def test_create_review_rating_too_high(client: AsyncClient):
    """Рейтинг выше 5 → 422."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Слишком высокий рейтинг для теста", "rating": 6},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_rating_zero(client: AsyncClient):
    """Рейтинг 0 → 422."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Нулевой рейтинг недопустим в тесте", "rating": 0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_rating_negative(client: AsyncClient):
    """Отрицательный рейтинг → 422."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Отрицательный рейтинг недопустим совсем", "rating": -1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_missing_text(client: AsyncClient):
    """Отсутствие text → 422."""
    response = await client.post("/api/reviews/", json={"rating": 5})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_missing_rating(client: AsyncClient):
    """Отсутствие rating → использует дефолт 5, создаётся успешно."""
    response = await client.post(
        "/api/reviews/",
        json={"text": "Отзыв без явного рейтинга использует дефолтное значение пять."},
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 5


# ===========================================================================
# GET /api/reviews/  (публичный — только одобренные)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_approved_reviews_empty(client: AsyncClient):
    """Пустой список если нет одобренных отзывов."""
    response = await client.get("/api/reviews/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_approved_reviews_filters_pending(
    client: AsyncClient, db_session: AsyncSession
):
    """Pending-отзывы не попадают в публичный список."""
    await create_review(
        db_session, "Одобренный публичный отзыв", status=ReviewStatus.APPROVED
    )
    await create_review(
        db_session, "Ожидающий модерации отзыв", status=ReviewStatus.PENDING
    )
    await create_review(
        db_session, "Отклонённый отзыв заведения", status=ReviewStatus.REJECTED
    )

    response = await client.get("/api/reviews/")
    assert response.status_code == 200
    texts = [r["text"] for r in response.json()]
    assert "Одобренный публичный отзыв" in texts
    assert "Ожидающий модерации отзыв" not in texts
    assert "Отклонённый отзыв заведения" not in texts


@pytest.mark.asyncio
async def test_get_approved_reviews_no_auth_required(client: AsyncClient):
    """Публичный доступ — токен не нужен."""
    response = await client.get("/api/reviews/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_approved_reviews_sorted_newest_first(
    client: AsyncClient, db_session: AsyncSession
):
    """Отзывы отсортированы от новых к старым (проверяем порядок ID как прокси)."""
    for i in range(3):
        await create_review(
            db_session, f"Одобренный отзыв номер {i}", status=ReviewStatus.APPROVED
        )

    response = await client.get("/api/reviews/")
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert ids == sorted(ids, reverse=True)


# ===========================================================================
# GET /api/reviews/all  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_all_reviews_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор видит абсолютно все отзывы независимо от статуса."""
    await create_review(db_session, "Все отзывы: pending", status=ReviewStatus.PENDING)
    await create_review(
        db_session, "Все отзывы: approved", status=ReviewStatus.APPROVED
    )

    response = await client.get("/api/reviews/all", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_all_reviews_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может смотреть все отзывы."""
    response = await client.get("/api/reviews/all", headers=auth_headers(client_token))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_all_reviews_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/reviews/all")
    assert response.status_code == 401


# ===========================================================================
# GET /api/reviews/pending  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_pending_reviews_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Возвращает только ожидающие модерации отзывы."""
    await create_review(
        db_session, "Ожидает модерации AdminOnly тест", status=ReviewStatus.PENDING
    )
    await create_review(
        db_session, "Уже одобренный отзыв в системе", status=ReviewStatus.APPROVED
    )

    response = await client.get(
        "/api/reviews/pending", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any(r["text"] == "Ожидает модерации AdminOnly тест" for r in results)
    # Одобренный НЕ должен попасть в список pending
    assert all(r["text"] != "Уже одобренный отзыв в системе" for r in results)


@pytest.mark.asyncio
async def test_get_pending_reviews_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может смотреть pending-отзывы."""
    response = await client.get(
        "/api/reviews/pending", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_pending_reviews_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/reviews/pending")
    assert response.status_code == 401


# ===========================================================================
# PATCH /api/reviews/{review_id}/status
# ===========================================================================


@pytest.mark.asyncio
async def test_change_review_status_to_approved(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор одобряет отзыв."""
    r = await create_review(db_session, "Хороший отзыв для одобрения модератором")
    response = await client.patch(
        f"/api/reviews/{r.id}/status",
        headers=auth_headers(admin_token),
        json={"status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_change_review_status_to_rejected(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор отклоняет отзыв."""
    r = await create_review(db_session, "Спамный отзыв для отклонения модератором")
    response = await client.patch(
        f"/api/reviews/{r.id}/status",
        headers=auth_headers(admin_token),
        json={"status": "rejected"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_change_review_status_invalid_value(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Неизвестный статус → 422."""
    r = await create_review(db_session, "Отзыв для теста невалидного статуса")
    response = await client.patch(
        f"/api/reviews/{r.id}/status",
        headers=auth_headers(admin_token),
        json={"status": "published"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_review_status_not_found(client: AsyncClient, admin_token: str):
    """Несуществующий отзыв → 404."""
    response = await client.patch(
        "/api/reviews/999999/status",
        headers=auth_headers(admin_token),
        json={"status": "approved"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_change_review_status_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может менять статус отзывов."""
    r = await create_review(db_session, "Отзыв для теста запрета смены статуса")
    response = await client.patch(
        f"/api/reviews/{r.id}/status",
        headers=auth_headers(client_token),
        json={"status": "approved"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_change_review_status_no_auth(
    client: AsyncClient, db_session: AsyncSession
):
    """Без токена → 401."""
    r = await create_review(db_session, "Отзыв для теста отсутствия токена авторизации")
    response = await client.patch(
        f"/api/reviews/{r.id}/status",
        json={"status": "approved"},
    )
    assert response.status_code == 401
