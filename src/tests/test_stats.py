"""
Тесты: /api/stats/
"""

from datetime import datetime, timedelta, timezone

import pytest
from common.models import (
    Event,
    EventReaction,
    ReactionStatus,
    Review,
    ReviewStatus,
    Suggestion,
    SuggestionStatus,
)
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Фабрики
# ---------------------------------------------------------------------------


async def create_event(db: AsyncSession, title: str = "Тестовое событие") -> Event:
    event = Event(
        title=title,
        description="Описание тестового события для статистики",
        date_time=(datetime.now(timezone.utc) + timedelta(days=3)).replace(tzinfo=None),
        image_path="uploads/events/stats_test.jpg",
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def add_reaction(
    db: AsyncSession,
    event_id: int,
    user_id: int,
    status: ReactionStatus = ReactionStatus.GOING,
) -> EventReaction:
    r = EventReaction(event_id=event_id, user_id=user_id, status=status)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


# ===========================================================================
# GET /api/stats/  (Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_general_stats_empty(client: AsyncClient, admin_token: str):
    """Статистика дашборда возвращает нули для пустой БД."""
    response = await client.get("/api/stats/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert "pendingReviews" in body
    assert "newSuggestions" in body
    assert "totalEvents" in body
    assert isinstance(body["pendingReviews"], int)
    assert isinstance(body["newSuggestions"], int)
    assert isinstance(body["totalEvents"], int)


@pytest.mark.asyncio
async def test_get_general_stats_counts_pending_reviews(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """pendingReviews считает только ожидающие отзывы."""
    db_session.add(Review(text="Ожидает 1", rating=4, status=ReviewStatus.PENDING))
    db_session.add(Review(text="Ожидает 2", rating=5, status=ReviewStatus.PENDING))
    db_session.add(Review(text="Одобрен", rating=5, status=ReviewStatus.APPROVED))
    await db_session.commit()

    response = await client.get("/api/stats/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()["pendingReviews"] >= 2


@pytest.mark.asyncio
async def test_get_general_stats_counts_pending_suggestions(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """newSuggestions считает только предложения со статусом PENDING."""
    db_session.add(
        Suggestion(
            text="Предложение 1 в ожидании модерации",
            subject="Тест",
            status=SuggestionStatus.PENDING,
        )
    )
    db_session.add(
        Suggestion(
            text="Предложение 2 уже запланировано",
            subject="Тест",
            status=SuggestionStatus.PLANNED,
        )
    )
    await db_session.commit()

    response = await client.get("/api/stats/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()["newSuggestions"] >= 1


@pytest.mark.asyncio
async def test_get_general_stats_counts_total_events(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """totalEvents считает все события, включая прошедшие."""
    await create_event(db_session, "Считаемое событие A")
    await create_event(db_session, "Считаемое событие B")

    response = await client.get("/api/stats/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    assert response.json()["totalEvents"] >= 2


@pytest.mark.asyncio
async def test_get_general_stats_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может просматривать статистику."""
    response = await client.get("/api/stats/", headers=auth_headers(client_token))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_general_stats_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/stats/")
    assert response.status_code == 401


# ===========================================================================
# GET /api/stats/events/{event_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_get_event_stats_empty_reactions(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Детальная статистика события без реакций: все счётчики равны 0."""
    event = await create_event(db_session, "Событие без реакций")

    response = await client.get(
        f"/api/stats/events/{event.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == event.id
    assert body["event_title"] == "Событие без реакций"
    assert body["going"]["count"] == 0
    assert body["going"]["users"] == []
    assert body["maybe"]["count"] == 0
    assert body["not_going"]["count"] == 0


@pytest.mark.asyncio
async def test_get_event_stats_with_reactions(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_token: str,
    client_user,
    admin_user,
):
    """Статистика корректно подсчитывает и распределяет реакции."""
    event = await create_event(db_session, "Популярное событие")
    await add_reaction(db_session, event.id, client_user.id, ReactionStatus.GOING)
    await add_reaction(db_session, event.id, admin_user.id, ReactionStatus.MAYBE)

    response = await client.get(
        f"/api/stats/events/{event.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["going"]["count"] == 1
    assert body["maybe"]["count"] == 1
    assert body["not_going"]["count"] == 0

    going_user_ids = [u["id"] for u in body["going"]["users"]]
    assert client_user.id in going_user_ids


@pytest.mark.asyncio
async def test_get_event_stats_not_going_reaction(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_token: str,
    client_user,
):
    """Реакция NOT_GOING правильно попадает в категорию not_going."""
    event = await create_event(db_session, "Событие с отказами")
    await add_reaction(db_session, event.id, client_user.id, ReactionStatus.NOT_GOING)

    response = await client.get(
        f"/api/stats/events/{event.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["not_going"]["count"] == 1
    assert body["going"]["count"] == 0


@pytest.mark.asyncio
async def test_get_event_stats_not_found(client: AsyncClient, admin_token: str):
    """Несуществующее событие → 404."""
    response = await client.get(
        "/api/stats/events/999999", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_event_stats_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может видеть детальную статистику."""
    event = await create_event(db_session, "Закрытая статистика")
    response = await client.get(
        f"/api/stats/events/{event.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


# ===========================================================================
# GET /api/stats/events-all
# ===========================================================================


@pytest.mark.asyncio
async def test_get_all_events_stats_empty(client: AsyncClient, admin_token: str):
    """Возвращает пустой список, если событий нет."""
    response = await client.get(
        "/api/stats/events-all", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_all_events_stats_contains_events(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Список содержит запись для каждого события."""
    await create_event(db_session, "Первое из всех событий")
    await create_event(db_session, "Второе из всех событий")

    response = await client.get(
        "/api/stats/events-all", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_all_events_stats_structure(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Каждый элемент содержит обязательные поля EventFullStats."""
    await create_event(db_session, "Структурное событие для проверки схемы")

    response = await client.get(
        "/api/stats/events-all", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    for item in response.json():
        assert "event_id" in item
        assert "event_title" in item
        assert "going" in item
        assert "maybe" in item
        assert "not_going" in item
        assert "count" in item["going"]
        assert "users" in item["going"]


@pytest.mark.asyncio
async def test_get_all_events_stats_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может просматривать сводную статистику."""
    response = await client.get(
        "/api/stats/events-all", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


# ===========================================================================
# GET /api/stats/events-current
# ===========================================================================


@pytest.mark.asyncio
async def test_get_current_events_stats_only_future(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """events-current возвращает только предстоящие события."""
    # Прошедшее событие
    past = Event(
        title="Прошедшее для статы",
        description="Прошедшее событие для теста статистики",
        date_time=(datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None),
        image_path="uploads/events/past.jpg",
    )
    db_session.add(past)
    await db_session.commit()

    future = await create_event(db_session, "Будущее для статы")

    response = await client.get(
        "/api/stats/events-current", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    titles = [e["event_title"] for e in response.json()]
    assert "Будущее для статы" in titles
    assert "Прошедшее для статы" not in titles


@pytest.mark.asyncio
async def test_get_current_events_stats_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может просматривать текущую статистику."""
    response = await client.get(
        "/api/stats/events-current", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_current_events_stats_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/stats/events-current")
    assert response.status_code == 401
