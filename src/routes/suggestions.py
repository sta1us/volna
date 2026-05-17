from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import Suggestion, User
from src.auth.dependencies import get_current_admin, get_current_user_or_none
from src.schemas.common import BaseMessageResponse
from src.schemas.suggestions import (
    SuggestionCreate,
    SuggestionRead,
    SuggestionStatus,
    SuggestionStatusUpdate,
)

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])


@router.post(
    "/", response_model=BaseMessageResponse, status_code=status.HTTP_201_CREATED
)
async def create_suggestion(
    data: SuggestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_none),
):
    """
    ## Отправить предложение или отзыв  (Доступ: Публичный)

    Эндпоинт доступен как авторизованным пользователям, так и анонимным гостям.

    Если запрос отправляет авторизованный пользователь, поля `guest_name` и `guest_contact`
    можно не передавать — система автоматически привяжет его `user_id`.

    ### Параметры:
    - **guest_name**: Имя гостя (если не авторизован)
    - **guest_contact**: Контактные данные гостя (телефон/соцсеть)"
    - **subject**: Тема обращения
    - **text**: Текст предложения

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    # Превращаем Pydantic-модель в словарь
    suggestion_dict = data.model_dump()

    if not current_user:
        # ИСПРАВЛЕНО: Жесткая валидация гостевых полей для предотвращения появления "пустых" строк
        if not data.guest_name or not data.guest_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для отправки гостевого обращения необходимо указать имя (guest_name).",
            )
        if not data.guest_contact or not data.guest_contact.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите контакты (guest_contact) для обратной связи.",
            )
        suggestion_dict["user_id"] = None
    else:
        # Автоматическая привязка данных авторизованного пользователя
        suggestion_dict["user_id"] = current_user.id
        suggestion_dict["guest_name"] = current_user.first_name
        suggestion_dict["guest_contact"] = (
            f"TG: @{current_user.username}"
            if current_user.username
            else f"TG ID: {current_user.tg_id}"
        )

    new_suggestion = Suggestion(
        **suggestion_dict, is_read=False, status=SuggestionStatus.PENDING
    )
    db.add(new_suggestion)
    await db.commit()

    return {
        "status": "success",
        "message": "Ваше обращение успешно принято и передано руководству заведения. Спасибо!",
    }


@router.get("/", response_model=list[SuggestionRead])
async def get_suggestions(
    is_read: Optional[bool] = None,
    status: Optional[SuggestionStatus] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Просмотр всех предложений (Доступ: Администратор)

    Возвращает список предложений, отсортированный от самых новых к самым старым.
    Поддерживает фильтрацию по статусу прочтения и по бизнес-статусу.

    ### Параметры:
    - **is_read** (Path): Флаг для выбора только прочитанных
    - **status** (Path): Фильтрация по статусу

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.

    ### Возвращает:
    - Массив объектов `SuggestionRead` (может быть пустым `[]`).
    """
    query = select(Suggestion)

    # Динамические фильтры для удобства админа
    if is_read is not None:
        query = query.where(Suggestion.is_read == is_read)
    if status is not None:
        query = query.where(Suggestion.status == status)

    query = query.order_by(Suggestion.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{suggestion_id}/read", response_model=BaseMessageResponse)
async def mark_suggestion_read(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Отметить предложение как прочитанное (Доступ: Администратор)

    Быстро переводит флаг `is_read` в состояние `True`.

    ### Параметры:
    - **suggestion_id** (Path): Идентификатор предложения.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Предложение с таким ID не существует.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found"
        )

    item.is_read = True
    await db.commit()
    return {"status": "success", "message": "Предложение отмечено как прочитанное."}


@router.patch("/{suggestion_id}/status", response_model=BaseMessageResponse)
async def change_suggestion_status(
    suggestion_id: int,
    data: SuggestionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Изменить статус обработки предложения (Доступ: Администратор)

    Позволяет перевести предложение в нужный статус (например: `ACCEPTED`, `REJECTED`, `COMPLETED`).

    ### Параметры:
    - **suggestion_id** (Path): Идентификатор предложения.
    - **status** (Path): Новый статус предложения.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Предложение с таким ID не существует.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found"
        )

    suggestion.status = data.status
    await db.commit()
    return {"status": "success", "message": f"Статус изменен на {data.status}"}


@router.delete(
    "/{suggestion_id}",
    response_model=BaseMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Удалить предложение (Доступ: Администратор)

    Безвозвратно удаляет запись предложения из базы данных.

    ### Параметры:
    - **suggestion_id** (Path): Идентификатор удаляемого предложения.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Предложение с таким ID не существует.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(Suggestion).where(Suggestion.id == suggestion_id))
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found"
        )

    await db.delete(suggestion)
    await db.commit()
    return {
        "status": "success",
        "message": f"Suggestion with ID {suggestion_id} successuffy deleted.",
    }
