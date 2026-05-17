from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from common.database import get_db
from common.models import (
    Event,
    EventReaction,
    ReactionStatus,
    Review,
    ReviewStatus,
    Suggestion,
    SuggestionStatus,
    User,
)
from src.auth.dependencies import get_current_admin
from src.schemas.stats import EventFullStats, GeneralStatsRead, UserShort

router = APIRouter(prefix="/stats", tags=["Stats"])


# --- ОБЩАЯ СТАТИСТИКА ПАНЕЛИ ---
@router.get("/", response_model=GeneralStatsRead)
async def get_stats(
    db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    """
    ## Получить общие агрегированные метрики для дашборда

    Запрашивает из базы данных количество необработанных отзывов, новых предложений
    и общее число событий. Подсчет выполняется на стороне СУБД через `COUNT`,
    что гарантирует высокую скорость работы.

    ### Ошибки:
    - **401 Unauthorized**: Отсутствует или невалиден токен авторизации.
    - **403 Forbidden**: У запрашивающего пользователя нет прав администратора.

     ### Возвращает:
    - **GeneralStatsRead**: Объект с тремя счетчиками (числа).
    """

    query_reviews = (
        select(func.count())
        .select_from(Review)
        .where(Review.status == ReviewStatus.PENDING)
    )
    query_suggs = (
        select(func.count())
        .select_from(Suggestion)
        .where(Suggestion.status == SuggestionStatus.PENDING)
    )
    query_events = select(func.count()).select_from(Event)

    res_reviews = await db.execute(query_reviews)
    res_suggs = await db.execute(query_suggs)
    res_events = await db.execute(query_events)

    return {
        "pendingReviews": res_reviews.scalar_one(),
        "newSuggestions": res_suggs.scalar_one(),
        "totalEvents": res_events.scalar_one(),
    }


# --- СТАТИСТИКА КОНКРЕТНОГО СОБЫТИЯ ---
@router.get("/events/{event_id}", response_model=EventFullStats)
async def get_event_reactions_stats(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Получить детальную статистику реакций на конкретное событие

    Выгружает списки пользователей, распределенные по трем категориям:
    "Пойду" (`going`), "Возможно" (`maybe`) и "Не пойду" (`not_going`).

    ### Параметры пути (Path):
    - **event_id** (int): Уникальный идентификатор события.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Событие с указанным ID не зарегистрировано в системе.

    ### Возвращает:
    - **EventFullStats**: Объект со списками пользователей и их количеством.
    """

    event_query = select(Event).where(Event.id == event_id)
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found "
        )

    # Подтягиваем реакции вместе с пользователями одним оптимизированным запросом
    reactions_query = (
        select(EventReaction)
        .where(EventReaction.event_id == event_id)
        .options(joinedload(EventReaction.user))
    )
    reactions_result = await db.execute(reactions_query)
    reactions = reactions_result.scalars().all()

    stats = {
        "event_id": event.id,
        "event_title": event.title,
        "going": {"count": 0, "users": []},
        "maybe": {"count": 0, "users": []},
        "not_going": {"count": 0, "users": []},
    }

    for r in reactions:
        if not r.user:
            continue

        user_info = UserShort.model_validate(r.user)

        if r.status == ReactionStatus.GOING:
            stats["going"]["count"] += 1
            stats["going"]["users"].append(user_info)
        elif r.status == ReactionStatus.MAYBE:
            stats["maybe"]["count"] += 1
            stats["maybe"]["users"].append(user_info)
        elif r.status == ReactionStatus.NOT_GOING:
            stats["not_going"]["count"] += 1
            stats["not_going"]["users"].append(user_info)

    return stats


# --- СТАТИСТИКА ПО ВСЕМ СОБЫТИЯМ ---
@router.get("/events-all", response_model=list[EventFullStats])
async def get_all_events_stats(
    db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    """
    ## Получить статистику реакций по ВСЕМ событиям (Архив)

    Выгружает полную историю всех событий и агрегирует списки откликнувшихся пользователей.
    Использует `joinedload` для предотвращения проблемы N+1 запросов к БД.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.

    ### Возвращает:
    - **list[EventFullStats]**: Массив объектов статистики для каждого события.
    """
    # Получаем все события, сразу подгружая связанные реакции и пользователей к ним
    query = select(Event).options(
        joinedload(Event.reactions).joinedload(EventReaction.user)
    )
    result = await db.execute(query)
    events = result.unique().scalars().all()

    all_stats = []
    for event in events:
        event_stats = {
            "event_id": event.id,
            "event_title": event.title,
            "going": {"count": 0, "users": []},
            "maybe": {"count": 0, "users": []},
            "not_going": {"count": 0, "users": []},
        }

        for r in event.reactions:
            if not r.user:
                continue

            user_info = UserShort.model_validate(r.user)

            if r.status == ReactionStatus.GOING:
                event_stats["going"]["count"] += 1
                event_stats["going"]["users"].append(user_info)
            elif r.status == ReactionStatus.MAYBE:
                event_stats["maybe"]["count"] += 1
                event_stats["maybe"]["users"].append(user_info)
            elif r.status == ReactionStatus.NOT_GOING:
                event_stats["not_going"]["count"] += 1
                event_stats["not_going"]["users"].append(user_info)

        all_stats.append(event_stats)

    return all_stats


# --- СТАТИСТИКА ПО ПРЕДСТОЯЩИМ СОБЫТИЯМ ---
@router.get("/events-current", response_model=list[EventFullStats])
async def get_current_events_stats(
    db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    """
    ## Получить статистику реакций только по ПРЕДСТОЯЩИМ событиям

    Фильтрует события, у которых дата проведения (`date_time`) больше или равна текущему моменту UTC.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.

    ### Возвращает:
    - **list[EventFullStats]**: Массив объектов статистики актуальных событий.
    """
    now_utc = datetime.now(timezone.utc)
    # Получаем все события, сразу подгружая связанные реакции и пользователей к ним
    query = (
        select(Event)
        .where(Event.date_time >= now_utc)
        .options(selectinload(Event.reactions).selectinload(EventReaction.user))
        .order_by(Event.date_time.asc())
    )

    result = await db.execute(query)
    events = result.unique().scalars().all()

    all_stats = []
    for event in events:
        event_stats = {
            "event_id": event.id,
            "event_title": event.title,
            "going": {"count": 0, "users": []},
            "maybe": {"count": 0, "users": []},
            "not_going": {"count": 0, "users": []},
        }

        for r in event.reactions:
            if not r.user:
                continue

            user_info = UserShort.model_validate(r.user)

            if r.status == ReactionStatus.GOING:
                event_stats["going"]["count"] += 1
                event_stats["going"]["users"].append(user_info)
            elif r.status == ReactionStatus.MAYBE:
                event_stats["maybe"]["count"] += 1
                event_stats["maybe"]["users"].append(user_info)
            elif r.status == ReactionStatus.NOT_GOING:
                event_stats["not_going"]["count"] += 1
                event_stats["not_going"]["users"].append(user_info)

        all_stats.append(event_stats)

    return all_stats
