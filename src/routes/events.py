import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import Event, EventReaction, ReactionStatus, User
from src.auth.dependencies import get_current_admin, get_current_user
from src.schemas.common import BaseMessageResponse
from src.schemas.events import (
    EventCreate,
    EventReactionRead,
    EventRead,
    EventUpdate,
    ReactionCreate,
    StatMessageResponse,
)

router = APIRouter(prefix="/events", tags=["Events"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "events"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_model=list[EventRead])
async def get_events(upcoming_only: bool = True, db: AsyncSession = Depends(get_db)):
    """
    ## Получить список событий (Доступ: Публичный)

    Возвращает список всех зарегистрированных мероприятий с сортировкой по дате (от ближайших к дальним).

    ### Параметры (Query):
    - **upcoming_only**: Если `True`, исключает завершенные события, сравнивая `date_time` с текущим временем UTC.

    ### Возвращает:
    - Массив объектов `EventRead` (может быть пустым `[]`).
    """
    query = select(Event)

    # Показываем только те события, которые еще не наступили
    if upcoming_only:
        query = query.where(Event.date_time >= datetime.now(timezone.utc))

    query = query.order_by(Event.date_time.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    ## Детальная информация о событии (Доступ: Публичный)

    Ищет событие в базе данных по его уникальному идентификатору (`id`).

    ### Параметры:
    - **event_id** (Path): Идентификатор события в БД.

    ### Ошибки:
    - **404 Not Found**: Если события с таким ID не существует.

    ### Возвращает:
    - Объект `EventRead` (может быть пустым `[]`).
    """
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.get("/{event_id}/stats", response_model=StatMessageResponse)
async def get_event_stats(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    ## Статистика откликов на событие (Доступ: Публичный)

    Агрегирует пользовательские реакции (пойду / возможно пойду) для конкретного мероприятия.

    ### Параметры:
    - **event_id** (Path): Идентификатор события.

    ### Возвращает: Обьект StatMessageResponse):
    - `total`: Общее количество пользователей, оставивших реакцию.
    - `going`: Количество подтвержденных участников.
    - `maybe`: Количество сомневающихся участников.
    """
    result = await db.execute(
        select(EventReaction.status).where(EventReaction.event_id == event_id)
    )
    reactions = result.scalars().all()

    return {
        "status": "success",
        "message": "Статистика успешно агрегирована.",
        "total": len(reactions),
        "going": reactions.count(ReactionStatus.GOING),
        "maybe": reactions.count(ReactionStatus.MAYBE),
    }


@router.post("/", response_model=EventRead)
async def create_event(
    event_data: EventCreate = Depends(EventCreate.as_form),
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    ## Создать новое событие (Доступ: Администратор)

    Принимает текстовые данные события в формате **Form Data** и изображение афиши.
    Файл сохраняется локально на сервере с генерацией случайного UUID-имени.

    ### Параметры Form-Data (`event_data`):
    - **title**: Заголовок (минимум 3 символа).
    - **description**: Текстовое описание.
    - **date_time**: Дата и время в формате ISO-8601 (например, `2026-12-31T20:00:00`).
    - **tg_file_id**: *(Опционально)* ID файла в Telegram для бота.

    ### Файлы:
    - **file**: Изображение/афиша мероприятия.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.

    ### Возвращает:
    - Объект `EventRead`.
    """
    # Сохраняем фото
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_event = Event(**event_data.model_dump(), image_path=str(file_path))

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    return new_event


@router.post("/{event_id}/react", response_model=EventReactionRead)
async def set_event_reaction(
    event_id: int,
    data: ReactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ## Установить/изменить реакцию на событие (Доступ: Пользователь)

    Позволяет авторизованному пользователю отметить свое участие.
    Если реакция на это событие от пользователя уже была — статус обновится.

    ### Параметры:
    - **event_id** (Path): Идентификатор события.
    - **status** (Body): Новый статус реакции (`going` или `maybe` или `not`).

    ### Ошибки:
    - **401 Unauthorized**: Пользователь не аутентифицирован.
    - **404 Not Found**: Указанное событие не существует.

    ### Возвращает:
    - Объект `EventReactionRead` (может быть пустым `[]`).
    """
    # 1. Проверяем, существует ли событие
    event_exists = await db.execute(select(Event).where(Event.id == event_id))
    if not event_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # 2. Ищем, была ли уже реакция от этого пользователя на это событие
    query = select(EventReaction).where(
        and_(
            EventReaction.event_id == event_id, EventReaction.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    reaction = result.scalar_one_or_none()

    if reaction:
        # Если реакция есть — обновляем статус (например, передумал)
        reaction.status = data.status
    else:
        # Если реакции нет — создаем новую
        reaction = EventReaction(
            event_id=event_id, user_id=current_user.id, status=data.status
        )
        db.add(reaction)

    await db.commit()
    await db.refresh(reaction)
    return reaction


# 2. Обновление события (используем PUT для замены данных)
@router.put("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    event_data: EventUpdate = Depends(EventUpdate.as_form),
    file: Optional[UploadFile] = File(None),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    ## Полное или частичное обновление события (Доступ: Администратор)

    Позволяет перезаписать поля существующего события. Передавать нужно все поля (так как это `PUT`),
    но загрузка новой картинки опциональна. Принимает текстовые данные события в формате **Form Data**.

    ### Параметры:
    - **event_id** (Path): Идентификатор редактируемого события.

    ### Параметры Form-Data (`event_data`):
    - **title**: Заголовок (минимум 3 символа).
    - **description**: Текстовое описание.
    - **date_time**: Дата и время в формате ISO-8601 (например, `2026-12-31T20:00:00`).
    - **tg_file_id**: *(Опционально)* ID файла в Telegram для бота.

    ### Файлы:
    - **file** (File): *(Опционально)* Новое изображение. Если передано, старый файл НЕ удаляется автоматически (нужно дописать логику удаления).

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Событие с таким ID не найдено.

    ### Возвращает:
    - Объект `EventRead`.
    """
    # Ищем событие в базе
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    db_event = result.scalar_one_or_none()

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Извлекаем только те поля, которые юзер РЕАЛЬНО передал в форме (исключаем None)
    update_dict = event_data.model_dump(exclude_unset=True)

    if file:
        # Логика автоматического удаления старого файла перед записью нового
        if db_event.image_path:
            old_file_path = Path(db_event.image_path)
            try:
                old_file_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Ошибка при очистке старого файла афиши {old_file_path}: {e}")

        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ИСПРАВЛЕНО: Приведение к str()
        update_dict["image_path"] = str(file_path)

    # Применяем все изменения одной строчкой!
    for key, value in update_dict.items():
        setattr(db_event, key, value)

    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.delete(
    "/{event_id}",
    response_model=BaseMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    ## Удалить событие (Доступ: Администратор)

    Удаляет событие из базы данных, а также физически стирает связанный файл изображения с диска сервера.

    ### Параметры:
    - **event_id** (Path): Идентификатор удаляемого события.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Если событие уже удалено или не существовало.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Удаляем файл
    if event.image_path:
        file_path = Path(event.image_path)
        try:
            file_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"Лог: Исключение при удалении афиши с диска: {e}")

    await db.delete(event)
    await db.commit()
    return {
        "status": "success",
        "message": f"Event with ID {event_id} successuffy deleted.",
    }
