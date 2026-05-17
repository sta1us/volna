import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import Location, User
from src.auth.dependencies import get_current_admin
from src.schemas.location import LocationFormPayload, LocationRead

router = APIRouter(prefix="/location", tags=["Location"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "location"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --- ПОЛУЧИТЬ ЛОКАЦИЮ (Публичный) ---
@router.get("/", response_model=LocationRead)
async def get_location(db: AsyncSession = Depends(get_db)):
    """
    ## Получить актуальные контактные данные и локацию заведения (Доступ: Публичный)

    Возвращает информацию о адресе, координатах (для интерактивных карт),
    режиме работы, телефонах и ссылках на изображения фасада/схем проезда.
    Этот эндпоинт является публичным.

    ### Ошибки:
    - **404 Not Found**: Информация о локации еще ни разу не заполнялась администратором.

    ### Возвращает:
    - **LocationRead**: Объект с заполненными контактами заведения.
    """
    result = await db.execute(select(Location))
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not set yet."
        )
    return location


# --- ОБНОВИТЬ ДАННЫЕ ЛОКАЦИИ (Admin / Form-Data Payload) ---
@router.put("/", response_model=LocationRead)
async def update_location(
    form_data: LocationFormPayload = Depends(LocationFormPayload.as_form),
    file_entrance: Optional[UploadFile] = File(
        None, description="Новая фотография входа/здания"
    ),
    file_map: Optional[UploadFile] = File(
        None, description="Новое статическое изображение карты/схемы проезда"
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Создать или обновить информацию о локации (Доступ: Администратор)

    Выполняет операцию Upsert (обновляет существующую запись или создает её, если таблица пуста).
    При отправке новых файлов старые изображения автоматически вычищаются с диска сервера.

    Данные передаются в формате `multipart/form-data`.

    ### Тело запроса (Form-Data fields из схемы LocationFormPayload):
    - **address**: Строка (обязательно).
    - **latitude** / **longitude**: Координаты типа Float (обязательно).
    - **working_hours** / **phone** / **email**: Текстовые контакты (опционально).
    - **file_entrance**: Файл изображения фасада (опционально).
    - **file_map**: Файл изображения карты (опционально).

    ### Ошибки:
    - **401 Unauthorized**: Пользователь не предоставил токен авторизации.
    - **403 Forbidden**: Пользователь авторизован, но не имеет прав администратора.
    - **422 Unprocessable Entity**: Ошибка валидации формата координат или превышение длины строк.

    ### Возвращает:
    - **LocationRead**: Обновленный объект локации с новыми данными и путями к файлам.
    """
    # Ищем существующую запись локации
    result = await db.execute(select(Location))
    location = result.scalar_one_or_none()

    # Если локации нет — инициализируем новую запись
    if not location:
        location = Location(
            address=form_data.address,
            latitude=form_data.latitude,
            longitude=form_data.longitude,
        )
        db.add(location)

    # Обновляем текстовые поля напрямую (исправлена ошибка «незатирания» полей при пустых строках)
    location.address = form_data.address
    location.latitude = form_data.latitude
    location.longitude = form_data.longitude
    location.working_hours = form_data.working_hours
    location.phone = form_data.phone
    location.email = form_data.email

    # Логика обработки файла фасада здания
    if file_entrance:
        if location.image_path:
            old_path = Path(location.image_path)
            try:
                old_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Ошибка удаления старого файла фасада: {e}")

        file_extension = Path(file_entrance.filename).suffix
        unique_filename = f"facade_{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_entrance.file, buffer)

        location.image_path = str(file_path)

    # Логика обработки файла схемы проезда
    if file_map:
        if location.map_image_path:
            old_path = Path(location.map_image_path)
            try:
                old_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Ошибка удаления старого файла карты: {e}")

        # Исправлен префикс на map_ для избежания путаницы в именах файлов
        file_extension = Path(file_map.filename).suffix
        unique_filename = f"map_{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_map.file, buffer)

        location.map_image_path = str(file_path)

    await db.commit()
    await db.refresh(location)
    return location
