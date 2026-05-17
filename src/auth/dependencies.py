from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import User, UserRole

# Указываем FastAPI, где брать токен (из заголовка Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/telegram")


# 1. Зависимость для получения ЛЮБОГО авторизованного пользователя
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        # Извлекаем id пользователя (обычно записывается в "sub")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Идем в базу данных и лениво достаем пользователя
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user  # Возвращает полноценный объект User


# 2. Зависимость для получения ЛЮБОГО авторизованного пользователя (иначе None)
async def get_current_user_or_none(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Необязательная зависимость для получения текущего пользователя.

    Если в заголовках передан валидный JWT-токен, возвращает объект User.
    Если токена нет, он протух или некорректен — функция молча возвращает None,
    не блокируя выполнение эндпоинта.
    """
    # 1. Пытаемся достать заголовок Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        # 2. Проверяем формат "Bearer <token>"
        scheme, token = auth_header.split(" ")
        if scheme.lower() != "bearer":
            return None

        # 3. Декодируем JWT-токен
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # 4. Достаем ID пользователя из payload (обычно это поле "sub")
        user_id: str = payload.get("sub")
        if not user_id:
            return None

    except (ValueError, JWTError):
        # Если токен "битый", некорректно разбит split() или истек (ExpiredSignatureError)
        return None

    # 5. Ищем пользователя в базе данных
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    return user


# 3. Зависимость ТОЛЬКО для админов (цепочка из get_current_user)
def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    # Здесь мы проверяем роль уже у реального объекта из базы
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас недостаточно прав для этого действия",
        )
    return current_user
