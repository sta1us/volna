from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import User, UserRole
from src.auth.dependencies import get_current_admin
from src.schemas.common import BaseMessageResponse
from src.schemas.users import UsersRead, UsersRoleUpdate

router = APIRouter(prefix="/users", tags=["Users"])


# Получить всех пользователей
@router.get("/", response_model=list[UsersRead])
async def get_all_users(
    db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)
):
    """
    ## Получить список всех пользователей (Доступ: Администратор)

    Возвращает полную базу данных пользователей, включая их роли и Telegram ID.

    ### Ошибки:
    - **401 Unauthorized**: Пользователь не авторизован.
    - **403 Forbidden**: У пользователя недостаточно прав (не админ).

    ### Возвращает:
    - Массив объектов `UsersRead` (может быть пустым `[]`).
    """
    query = select(User)
    result = await db.execute(query)
    return result.scalars().all()


# Смена роли
@router.patch("/{user_id}/role", response_model=UsersRead)
async def update_user_role(
    user_id: int,
    data: UsersRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    ## Изменить роль пользователя (Доступ: Администратор)

    Позволяет повысить пользователя до `ADMIN` или понизить до `CLIENT`.
    Внедрена защита от случайного снятия прав с самого себя.

    ### Параметры:
    - **user_id** (Path): ID целевого пользователя, у которого меняется роль.
    - **role** (Body): Новая роль из доступного перечня (`ADMIN`, `CLIENT`).

    ### Ошибки:
    - **400 Bad Request**: Попытка снять права администратора с самого себя.
    - **404 Not Found**: Пользователь с указанным ID не найден.

    ### Возвращает:
    - Объект `UsersRead`.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Запрещаем снимать админа с самого себя, чтобы не потерять доступ
    if user.id == current_admin.id and data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы не можете снять права админа с самого себя",
        )

    user.role = data.role
    await db.commit()
    await db.refresh(user)
    return user


# Удаление
@router.delete(
    "/{user_id}",
    response_model=BaseMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    ## Удалить пользователя (Доступ: Администратор)

    Полностью удаляет учетную запись пользователя из базы данных.
    Внедрена защита от удаления собственного аккаунта.

    ### Параметры:
    - **user_id** (Path): ID пользователя, которого нужно удалить.

    ### Ошибки:
    - **400 Bad Request**: Попытка удалить собственную учетную запись.
    - **404 Not Found**: Пользователь с указанным ID не найден.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить свою учетную запись",
        )

    await db.delete(user)
    await db.commit()
    return {
        "status": "success",
        "message": f"User with ID {user_id} successuffy deleted.",
    }
