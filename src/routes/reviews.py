from typing import Optional

from common.database import get_db
from common.models import Review, ReviewStatus, User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import get_current_admin, get_current_user_or_none
from src.schemas.common import BaseMessageResponse
from src.schemas.reviews import (
    AdminReviewRead,
    ReviewCreate,
    ReviewRead,
    ReviewStatusUpdate,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewRead)
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_none),
):
    """
    ## Оставить отзыв о заведении (Доступ: всем пользователям (авторизованным и гостям)).
    Все новые отзывы создаются со статусом `PENDING` и попадают на модерацию.

    ### Параметры тела запроса (JSON):
    - **text**: Текст отзыва (обязательно).
    - **rating**: Оценка работы (целое число от 1 до 5, по умолчанию 5).
    - **is_anonymous**: Если `true` и пользователь авторизован, его имя не будет отображаться.
    - **guest_name** / **guest_contact**: Заполняются только неавторизованными гостями.

    ### Ошибки:
    - **422 Unprocessable Entity**: Если `rating` меньше 1 или больше 5.

    ### Возвращает:
    Объект созданного отзыва со статусом `pending`.
    """
    new_review = Review(
        text=review_data.text,
        rating=review_data.rating,
        status=ReviewStatus.PENDING,  # Всегда ждет модерации
    )

    if current_user:
        # Если юзер в системе, привязываем его ID
        new_review.user_id = current_user.id
        # Если он не выбрал анонимность, можно также сохранить его имя в guest_name для истории
        if not review_data.is_anonymous:
            # На всякий случай сохраняем имя в guest_name, чтобы фронтенду было проще читать
            new_review.guest_name = current_user.first_name
        else:
            new_review.guest_name = "Анонимный пользователь"

    else:
        new_review.guest_name = review_data.guest_name or "Гость"
        new_review.guest_contact = review_data.guest_contact

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review


@router.get("/all", response_model=list[AdminReviewRead])
async def get_all_reviews(
    db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    """
    ## Получить полный архив отзывов (Доступ: Администратор)

    Возвращает абсолютно все отзывы из базы данных (включая одобренные, отклоненные и новые).

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.

    ### Возвращает:
    Полный список отзывов.
    """
    result = await db.execute(select(Review).order_by(Review.created_at.desc()))
    return result.scalars().all()


@router.get("/pending", response_model=list[ReviewRead])
async def get_pending_reviews(
    db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)
):
    """
    ## Получить список отзывов, ожидающих проверки (Доступ: Администратор)

    Возвращает список всех новых отзывов (`status == pending`), которые еще не промодерированы.

    ### Ошибки:
    - **401 Unauthorized**: Не передан токен авторизации.
    - **403 Forbidden**: Пользователь не является администратором.

    ### Возвращает:
    Массив объектов отзывов для админ-панели.
    """
    result = await db.execute(
        select(Review)
        .where(Review.status == ReviewStatus.PENDING)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()


# 2. Получить список ОДОБРЕННЫХ отзывов (Для сайта)
@router.get("/", response_model=list[ReviewRead])
async def get_approved_reviews(db: AsyncSession = Depends(get_db)):
    """
    ## Получить список одобренных отзывов для сайта  (Доступ: Публичный)

    Возвращает список отзывов, которые прошли модерацию (`status == approved`).
    Результаты отсортированы по дате: от самых свежих к более старым.

    ### Возвращает:
    Массив объектов отзывов (может быть пустым `[]`).
    """
    result = await db.execute(
        select(Review)
        .where(Review.status == ReviewStatus.APPROVED)
        .order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{review_id}/status", response_model=BaseMessageResponse)
async def change_review_status(
    review_id: int,
    data: ReviewStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Изменить статус отзыва / Модерация (Доступ: Администратор)

    Позволяет одобрить отзыв для публикации на сайте или отклонить его.

    ### Параметры пути (Path):
    - **review_id**: ID модерируемого отзыва.

    ### Параметры тела запроса (JSON):
    - **status**: Новое значение из перечисления `ReviewStatus` (`approved` или `rejected`).

    ### Ошибки:
    - **401/403**: Ошибки прав доступа.
    - **404 Not Found**: Отзыв с указанным `review_id` не существует в базе данных.

    ### Возвращает:
    Объект `BaseMessageResponse` с подтверждением успешного изменения статуса.
    """
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found "
        )

    review.status = data.status
    await db.commit()
    return {
        "status": "success",
        "message": f"Статус отзыва успешно изменен на {data.status}.",
    }


@router.delete(
    "/{review_id}",
    response_model=BaseMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Удалить отзыв (Доступ: Администратор)

    Безвозвратно удаляет отзыв из базы данных.

    ### Параметры:
    - **review_id** (Path): Идентификатор удаляемого отзыва.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Отзыв с таким ID не существует.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    await db.delete(review)
    await db.commit()
    return {
        "status": "success",
        "message": f"Review with ID {review_id} successuffy deleted.",
    }
