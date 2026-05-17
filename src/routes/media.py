import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import Media, MediaType, User
from src.auth.dependencies import get_current_admin
from src.schemas.common import BaseMessageResponse
from src.schemas.media import MediaRead, UploadMediaMessageResponse

router = APIRouter(prefix="/media", tags=["Media"])

# Инициализация путей через pathlib
UPLOAD_DIR_MAIN = Path(settings.UPLOAD_DIR) / "media"
UPLOAD_DIR_EVENTS = Path(settings.UPLOAD_DIR) / "events" / "gallery"
UPLOAD_DIR_MAIN.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR_EVENTS.mkdir(parents=True, exist_ok=True)

# Разрешенные форматы
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".webp"],
    "video": [".mp4", ".mov", ".webm"],
}


# --- ОБЩАЯ ГАЛЕРЕЯ ---
@router.get("/gallery", response_model=list[MediaRead])
async def get_gallery(db: AsyncSession = Depends(get_db)):
    """
    ## Получить общую медиа-галерею заведения (Доступ: Публичный)

    Возвращает список всех изображений и видео, которые **не привязаны** к конкретным событиям
    (например, фотографии интерьера, основного меню, общие промо-ролики).

    ### Возвращает:
    - **list[MediaRead]**: Массив объектов медиафайлов с относительными URL-ссылками.
    """
    # Фильтруем те, что без привязки к событию
    query = (
        select(Media).where(Media.event_id.is_(None)).order_by(Media.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


# --- ГАЛЕРЕЯ КОНКРЕТНОГО СОБЫТИЯ ---
@router.get("/{event_id}", response_model=list[MediaRead])
async def get_event_gallery(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    ## Получить фотоотчет/медиа конкретного события (Доступ: Публичный)

    Возвращает список всех медиафайлов (картинок и видео), привязанных к указанному мероприятию.

    ### Параметры пути (Path):
    - **event_id** (int): Идентификатор события, галерею которого нужно выгрузить.

    ### Возвращает:
    - **list[MediaRead]**: Список медиафайлов, относящихся к событию.
    """
    # Фильтруем те, что без привязки к событию
    query = (
        select(Media)
        .where(Media.event_id == event_id)
        .order_by(Media.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/upload-multiple",
    response_model=UploadMediaMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_multiple_media(
    event_id: Optional[int] = Form(
        None,
        description="ID события, если файлы загружаются целенаправленно в его альбом",
    ),
    caption: Optional[str] = Form(
        None,
        max_length=200,
        description="Короткая текстовая подпись для всех файлов из текущего пакета",
    ),
    files: list[UploadFile] = File(
        ..., description="Массив загружаемых файлов (изображения/видео)"
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Пакетная загрузка медиафайлов (Доступ: Администратор)

    Принимает метаданные формы и массив файлов (Multipart Form Data).
    Автоматически определяет тип контента (картинка или видео) по расширению.

    ### Параметры формы (вынесены в схему MediaUploadPayload):
    - **event_id**: ID альбома события. Если пустой — файлы идут в общую галерею.
    - **caption**: Текстовое описание к медиафайлам.
    """
    results = []

    upload_dir = UPLOAD_DIR_EVENTS if event_id else UPLOAD_DIR_MAIN

    for file in files:
        file_ext = Path(file.filename).suffix.lower()

        m_type = None
        if file_ext in ALLOWED_EXTENSIONS["image"]:
            m_type = MediaType.IMAGE
        elif file_ext in ALLOWED_EXTENSIONS["video"]:
            m_type = MediaType.VIDEO
        else:
            results.append(
                {"filename": file.filename, "status": "skipped (unsupported format)"}
            )
            continue

        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Создание записи в БД
        new_media = Media(
            event_id=event_id,
            user_id=admin.id,
            caption=caption,
            tg_file_id=None,
            file_path=str(file_path),
            media_type=m_type,
        )
        db.add(new_media)
        results.append({"filename": file.filename, "status": "success"})

    await db.commit()
    return {
        "status": "success",
        "message": "Медиафайлы успешно обработаны.",
        "uploaded": results,
    }


# --- ПАКЕТНОЕ УДАЛЕНИЕ МЕДИА ---
@router.delete(
    "/delete-multiple",
    response_model=BaseMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_multiple_media(
    media_ids: list[int] = Body(
        ..., description="Список ID медиафайлов, которые нужно удалить"
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Пакетное удаление медиафайлов (Доступ: Администратор)

    Принимает массив ID в теле запроса (JSON Array). Находит записи в базе данных,
    физически стирает соответствующие файлы с диска сервера, а затем удаляет строки из БД.

    Если физический файл отсутствует на диске, запись из базы все равно будет удалена.

    ### Параметры тела запроса (JSON):
    - **media_ids**: Массив целых чисел `[1, 2, 3...]` (обязательно).

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Если ни один из переданных ID файлов не был найден в системе.

    ### Возвращает:
    - **BaseMessageResponse**: Текстовое подтверждение с указанием точного количества удаленных объектов.
    """

    # 1. Находим все существующие записи в базе
    query = select(Media).where(Media.id.in_(media_ids))
    result = await db.execute(query)
    media_items = result.scalars().all()

    if not media_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Указанные медиафайлы не найдены в системе",
        )

    deleted_count = 0
    for item in media_items:
        # 2. Удаляем физический файл с диска через pathlib
        if item.file_path:
            file_path = Path(item.file_path)
            try:
                file_path.unlink(missing_ok=True)
            except Exception as e:
                # Логируем ошибку файловой системы, но не прерываем транзакцию БД
                print(f"Ошибка при удалении файла {file_path}: {e}")

        # 3. Удаляем запись из БД
        await db.delete(item)
        deleted_count += 1

    await db.commit()

    return {
        "status": "success",
        "message": f"{deleted_count} медиафайлов успешно удалено.",
    }
