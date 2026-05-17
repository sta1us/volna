import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import MenuCategory, MenuPage, User
from src.auth.dependencies import get_current_admin
from src.schemas.common import BaseMessageResponse
from src.schemas.menu import MenuPageRead

router = APIRouter(prefix="/menu", tags=["Menu"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "menu"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/", response_model=MenuPageRead, status_code=status.HTTP_201_CREATED)
async def upload_menu_page(
    category: MenuCategory = Form(
        ...,
        description="Категория меню: кухня (kitchen) или бар (bar)",
    ),
    order_num: int = Form(
        0,  # значение по умолчанию
        ge=0,
        le=10000,
        description="Порядковый номер для сортировки при отображении (от 0 до 10000)",
    ),
    file: UploadFile = File(..., description="Файл изображения страницы меню"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Загрузить страницу меню (Доступ: Администратор)

    Создает новую страницу меню (загружает изображение) для указанной категории (Кухня/Бар).
    Файлы сохраняются на сервере с автоматической генерацией уникального UUID.

    ### Параметры Form-Data:
    - **category**: Принимает значения `kitchen` или `bar`.
    - **order_num**: Число для ручной сортировки страниц (например, чтобы салат шел перед десертом).

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **400 Bad Request**: Если загруженный файл не является изображением.

    ### Возвращает:
    - Обьект `MenuPageRead`.
    """
    # 1. Проверяем формат файла
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Разрешены только изображения",
        )

    # 2. Генерируем уникальное имя файла
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # 3. Сохраняем файл на диск
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Записываем в базу данных
    new_page = MenuPage(
        category=category,
        image_path=str(file_path),
        order_num=order_num,
    )
    db.add(new_page)
    await db.commit()
    await db.refresh(new_page)

    return new_page


@router.get("/", response_model=list[MenuPageRead])
async def get_menu(
    category: MenuCategory | None = None, db: AsyncSession = Depends(get_db)
):
    """
    ## Получить список страниц меню (Доступ: Публичный)

    Возвращает отсортированный список страниц меню. Доступно без авторизации.

    ### Параметры:
    - **category** (Query, опционально): Фильтр по категории (`kitchen` или `bar`). Если не передан — вернутся все страницы.

    ### Сортировка:
    - Результат всегда отсортирован по возрастанию поля `order_num`.

    ### Возвращает:
    - Массив объектов `MenuPageRead` (может быть пустым `[]`).
    """
    query = select(MenuPage)
    if category:
        query = query.where(MenuPage.category == category)

    query = query.order_by(MenuPage.order_num)
    result = await db.execute(query)
    return result.scalars().all()


@router.delete(
    "/{page_id}", response_model=BaseMessageResponse, status_code=status.HTTP_200_OK
)
async def delete_menu_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Удалить страницу меню (Доступ: Администратор)

    Удаляет запись о странице меню из базы данных, а также физически стирает файл картинки с сервера.

    ### Параметры:
    - **page_id** (Path): ID удаляемой страницы меню.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Если страница меню с таким ID не найдена.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    # 1. Ищем страницу в базе
    result = await db.execute(select(MenuPage).where(MenuPage.id == page_id))
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Menu page not found"
        )

    # 2. Удаляем файл с диска
    if page.image_path:
        file_path = Path(page.image_path)
        try:
            file_path.unlink(missing_ok=True)
        except Exception as e:
            # Логируем ошибку файловой системы, но транзакцию в БД не прерываем,
            # чтобы не заблокировать удаление «битой» записи
            print(f"Лог: Ошибка физического удаления файла меню {file_path}: {e}")

    # 3. Удаляем запись из БД
    await db.delete(page)
    await db.commit()

    return {
        "status": "success",
        "message": "Menu page successuffy deleted.",
    }
