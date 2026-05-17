import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import User, UserRole
from src.auth.dependencies import get_current_user
from src.auth.utils import create_access_token, verify_telegram_auth
from src.schemas.auth import (
    AdminVerificationResponse,
    TelegramAuthPayload,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(data: TelegramAuthPayload, db: AsyncSession = Depends(get_db)):
    """
    ## Авторизация / Регистрация через Telegram (Widget / Mini App) (Доступ: Публичный)

    Принимает валидные данные от Telegram. Если пользователь заходит в систему впервые,
    для него автоматически создается учетная запись. Если пользователь уже зарегистрирован,
    его профиль (first_name, username) обновляется до актуального состояния.

    Пользователю автоматически присваивается роль `ADMIN`, если его Telegram ID совпадает
    со значением `ADMIN_TG_ID` из конфигурационного файла окружения.

    ### Параметры тела запроса (JSON):
    - **id**: Telegram ID пользователя (обязательно).
    - **first_name** / **username**: Текущие данные профиля (опционально).
    - **auth_date** / **hash**: Данные проверки подлинности сессии.

    ### Ошибки:
    - **422 Unprocessable Entity**: Переданы некорректные типы данных, превышена длина строк.

    ### Возвращает:
    - **TokenResponse**: JWT-токен доступа, тип токена и установленная роль.
    """
    # 1. ЗАЩИТА: Проверка времени жизни сессии (Защита от Replay-атак)
    current_timestamp = int(time.time())
    if current_timestamp - data.auth_date > settings.TELEGRAM_AUTH_MAX_AGE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Авторизационная сессия истекла. Пожалуйста, попробуйте войти снова.",
        )

    # 2. ЗАЩИТА: Криптографическая проверка хэша данных
    # .model_dump() превращает Pydantic-модель в обычный dict
    if not verify_telegram_auth(data.model_dump()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка верификации данных. Данные подделаны.",
        )

    tg_id = data.id

    # Ищем пользователя в базе по его tg_id
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()

    # Динамически определяем, должен ли этот пользователь быть админом
    target_role = UserRole.ADMIN if tg_id == settings.ADMIN_TG_ID else UserRole.CLIENT

    if not user:
        # Сценарий 1: Первичная регистрация (Создание)
        user = User(
            tg_id=tg_id,
            username=data.username,
            first_name=data.first_name,
            role=target_role,
        )
        db.add(user)
    else:
        # Сценарий 2: Повторный вход (Актуализация данных из Telegram)
        user.username = data.username
        user.first_name = data.first_name
        # Меняем роль на ADMIN из .env только если текущая роль CLIENT.
        # Это защитит других администраторов (выданных через БД) от случайного разжалования.
        if tg_id == settings.ADMIN_TG_ID and user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN

    await db.commit()

    # Генерация JWT-токена. Рекомендуется зашивать внутренний user.id, а не tg_id
    token_payload = {"sub": str(user.id), "tg_id": user.tg_id, "role": user.role.value}
    token = create_access_token(token_payload)

    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.get("/verify-admin", response_model=AdminVerificationResponse)
async def verify_admin(current_user: User = Depends(get_current_user)):
    """
    ## Проверить, является ли текущий пользователь администратором (Доступ: Администратор)

    Используется клиентской частью (SPA/фронтендом панели управления) для быстрой
    проверки валидности JWT-токена и верификации роли администратора перед отрисовкой UI.

    ### Заголовки (Headers):
    - **Authorization**: `Bearer <token>` (обязательно).

    ### Ошибки:
    - **401 Unauthorized**: Передан невалидный, поврежденный или просроченный токен.
    - **403 Forbidden**: Токен валиден, но пользователь не обладает правами администратора.

    ### Возвращает:
    - **AdminVerificationResponse**: Флаг `is_admin: true`.
    """

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора.",
        )

    return {"is_admin": True}
