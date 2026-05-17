import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.database import get_db
from common.models import TeamMember, User
from src.auth.dependencies import get_current_admin
from src.schemas.common import BaseMessageResponse
from src.schemas.team import (
    TeamMemberCreate,
    TeamMemberRead,
    TeamMemberUpdate,
)

router = APIRouter(prefix="/team", tags=["Team"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "team"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --- СПИСОК КОМАНДЫ (Для всех) ---
@router.get("/", response_model=list[TeamMemberRead])
async def get_team(db: AsyncSession = Depends(get_db)):
    """
    ## Получить список всех сотрудников (Доступ: Публичный)

    Возвращает список всей команды, отсортированный по приоритету `order_priority`
    (сотрудники с большим числом идут в самом начале списка).

    ### Возвращает:
    - Массив объектов `TeamMemberRead` (может быть пустым `[]`).
    """
    # Сортируем по приоритету (от большего к меньшему)
    result = await db.execute(
        select(TeamMember).order_by(TeamMember.order_priority.desc())
    )
    return result.scalars().all()


@router.get("/{member_id}", response_model=TeamMemberRead)
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    """
    ## Получить детальную информацию о сотруднике (Доступ: Публичный)

    Ищет сотрудника по его уникальному ID.

    ### Ошибки:
    - **404 Not Found**: Если сотрудник с таким ID не зарегистрирован.

    ### Возвращает:
    - Обьект `TeamMemberRead`.
    """
    query = select(TeamMember).where(TeamMember.id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TeamMember not found"
        )
    return member


# --- ДОБАВИТЬ СОТРУДНИКА (Admin) ---
@router.post("/", response_model=TeamMemberRead, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    form_data: TeamMemberCreate = Depends(TeamMemberCreate.as_form),
    file: UploadFile = File(..., description="Фотография сотрудника"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Добавить нового сотрудника в команду (Доступ: Администратор)

    Принимает анкетные данные через Form Data и загружает изображение профиля.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.

    ### Возвращает:
    - Объект `TeamMemberRead`.
    """
    # Сохраняем фото
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_member = TeamMember(**form_data.model_dump(), image_path=str(file_path))

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member


@router.put("/{member_id}", response_model=TeamMemberRead)
async def update_member(
    member_id: int,
    form_data: TeamMemberUpdate = Depends(TeamMemberUpdate.as_form),
    file: Optional[UploadFile] = File(
        None, description="Новая фотография (опционально)"
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Изменить данные сотрудника (Доступ: Администратор)

    Позволяет обновить любые текстовые поля анкеты или загрузить новую фотографию.
    Передавать можно только измененные поля, остальные останутся нетронутыми.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Сотрудник с указанным ID не найден.

    ### Возвращает:
    - Объект `TeamMemberRead`.
    """
    query = select(TeamMember).where(TeamMember.id == member_id)
    result = await db.execute(query)
    db_member = result.scalar_one_or_none()

    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    update_dict = form_data.model_dump(exclude_unset=True)

    if file:
        # Сохраняем фото
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_dict["image_path"] = str(file_path)

    for key, value in update_dict.items():
        setattr(db_member, key, value)

    await db.commit()
    await db.refresh(db_member)
    return db_member


# --- УДАЛИТЬ СОТРУДНИКА (Admin) ---
@router.delete(
    "/{member_id}",
    response_model=BaseMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_team_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    ## Удалить сотрудника из команды (Доступ: Администратор)

    Удаляет анкету сотрудника из базы данных и полностью стирает файл его фотографии с диска.

    ### Параметры:
    - **member_id** (Path): Идентификатор удаляемого члена команды.

    ### Ошибки:
    - **401/403**: Ошибки авторизации администратора.
    - **404 Not Found**: Сотрудник с таким ID не существует.

    ### Возвращает:
    - Объект `BaseMessageResponse` = `status` + `message`.
    """
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id))
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Сотрудник не найден"
        )

    # Удаляем файл
    file_path = Path(member.image_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(member)
    await db.commit()
    return {
        "status": "success",
        "message": f"Member with ID {member_id} successuffy deleted.",
    }
