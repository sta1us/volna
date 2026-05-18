"""
Тесты: /api/team/
"""

import io

import pytest
from common.models import TeamMember
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers

# ---------------------------------------------------------------------------
# Фабрика члена команды
# ---------------------------------------------------------------------------


async def create_member(
    db: AsyncSession,
    first_name: str = "Иван",
    last_name: str = "Петров",
    role: str = "Шеф-повар",
    order_priority: int = 0,
) -> TeamMember:
    member = TeamMember(
        first_name=first_name,
        last_name=last_name,
        role=role,
        description="Опытный специалист с многолетним стажем работы",
        image_path="uploads/team/test.jpg",
        order_priority=order_priority,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


def fake_photo(name: str = "photo.jpg") -> tuple:
    return (name, io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 50), "image/jpeg")


# ===========================================================================
# GET /api/team/
# ===========================================================================


@pytest.mark.asyncio
async def test_get_team_empty(client: AsyncClient):
    """Публичный эндпоинт возвращает пустой список, если команды нет."""
    response = await client.get("/api/team/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_team_returns_members(client: AsyncClient, db_session: AsyncSession):
    """Возвращает список всех сотрудников."""
    await create_member(db_session, "Алексей", "Сидоров", "Бармен")
    await create_member(db_session, "Мария", "Иванова", "Менеджер")

    response = await client.get("/api/team/")
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_team_sorted_by_order_priority_desc(
    client: AsyncClient, db_session: AsyncSession
):
    """Сотрудники отсортированы по убыванию order_priority."""
    await create_member(db_session, "Низкий", "Приоритет", order_priority=1)
    await create_member(db_session, "Средний", "Приоритет", order_priority=5)
    await create_member(db_session, "Высокий", "Приоритет", order_priority=10)

    response = await client.get("/api/team/")
    assert response.status_code == 200
    priorities = [m["order_priority"] for m in response.json()]
    assert priorities == sorted(priorities, reverse=True)


@pytest.mark.asyncio
async def test_get_team_member_has_full_name(
    client: AsyncClient, db_session: AsyncSession
):
    """Объект сотрудника содержит вычисляемое поле full_name."""
    await create_member(db_session, "Дмитрий", "Козлов")

    response = await client.get("/api/team/")
    assert response.status_code == 200
    member = next(m for m in response.json() if m["first_name"] == "Дмитрий")
    assert "full_name" in member
    assert "Козлов" in member["full_name"]
    assert "Дмитрий" in member["full_name"]


@pytest.mark.asyncio
async def test_get_team_no_auth_required(client: AsyncClient):
    """Список команды доступен без авторизации."""
    response = await client.get("/api/team/")
    assert response.status_code == 200


# ===========================================================================
# GET /api/team/{member_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_get_member_by_id(client: AsyncClient, db_session: AsyncSession):
    """Возвращает детальную информацию о конкретном сотруднике."""
    member = await create_member(db_session, "Ольга", "Новикова", "Официант")

    response = await client.get(f"/api/team/{member.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == member.id
    assert body["first_name"] == "Ольга"
    assert body["role"] == "Официант"


@pytest.mark.asyncio
async def test_get_member_not_found(client: AsyncClient):
    """Несуществующий ID → 404."""
    response = await client.get("/api/team/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_member_with_middle_name(
    client: AsyncClient, db_session: AsyncSession
):
    """Сотрудник с отчеством: full_name содержит все три части."""
    member = TeamMember(
        first_name="Сергей",
        last_name="Фёдоров",
        middle_name="Николаевич",
        role="Су-шеф",
        description="Заместитель шеф-повара с большим опытом",
        image_path="uploads/team/fedorov.jpg",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    response = await client.get(f"/api/team/{member.id}")
    assert response.status_code == 200
    body = response.json()
    assert "Николаевич" in body["full_name"]


# ===========================================================================
# POST /api/team/  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_add_team_member_as_admin(client: AsyncClient, admin_token: str):
    """Администратор добавляет нового сотрудника."""
    response = await client.post(
        "/api/team/",
        headers=auth_headers(admin_token),
        data={
            "first_name": "Екатерина",
            "last_name": "Смирнова",
            "role": "Кондитер",
            "description": "Специалист по десертам и выпечке",
            "order_priority": "3",
        },
        files={"file": fake_photo()},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Екатерина"
    assert body["role"] == "Кондитер"
    assert "image_path" in body
    assert "image_url" in body


@pytest.mark.asyncio
async def test_add_team_member_with_middle_name(client: AsyncClient, admin_token: str):
    """Добавление сотрудника с отчеством."""
    response = await client.post(
        "/api/team/",
        headers=auth_headers(admin_token),
        data={
            "first_name": "Виктор",
            "last_name": "Зайцев",
            "middle_name": "Андреевич",
            "role": "Сомелье",
            "description": "Эксперт по вину и напиткам заведения",
            "order_priority": "5",
        },
        files={"file": fake_photo("viktor.jpg")},
    )
    assert response.status_code == 201
    assert response.json()["middle_name"] == "Андреевич"


@pytest.mark.asyncio
async def test_add_team_member_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может добавлять сотрудников."""
    response = await client.post(
        "/api/team/",
        headers=auth_headers(client_token),
        data={
            "first_name": "Незаконный",
            "last_name": "Сотрудник",
            "role": "Хакер",
            "description": "Попытка добавить сотрудника без прав",
        },
        files={"file": fake_photo()},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_team_member_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.post(
        "/api/team/",
        data={
            "first_name": "Аноним",
            "last_name": "Аноним",
            "role": "Аноним",
            "description": "Анонимная попытка добавить сотрудника",
        },
        files={"file": fake_photo()},
    )
    assert response.status_code == 401


# ===========================================================================
# PUT /api/team/{member_id}  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_update_team_member_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор обновляет данные сотрудника."""
    member = await create_member(db_session, "Старое", "Имя", "Старая должность")

    response = await client.put(
        f"/api/team/{member.id}",
        headers=auth_headers(admin_token),
        data={
            "first_name": "Старое",
            "last_name": "Имя",
            "role": "Новая должность",
            "description": "Обновлённое описание для теста",
            "order_priority": "0",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "Новая должность"


@pytest.mark.asyncio
async def test_update_team_member_with_new_photo(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Обновление сотрудника с заменой фотографии."""
    member = await create_member(db_session, "Фото", "Обновление")

    response = await client.put(
        f"/api/team/{member.id}",
        headers=auth_headers(admin_token),
        data={
            "first_name": "НовоеФото",
            "last_name": "Обновление",
            "role": "Шеф-повар",
            "description": "Описание для теста обновления с фото",
            "order_priority": "0",
        },
        files={"file": fake_photo("new_photo.jpg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "НовоеФото"
    assert "uploads/team" in body["image_path"]  # путь обновлён, UUID-имя


@pytest.mark.asyncio
async def test_update_team_member_not_found(client: AsyncClient, admin_token: str):
    """Обновление несуществующего сотрудника → 404."""
    response = await client.put(
        "/api/team/999999",
        headers=auth_headers(admin_token),
        data={
            "first_name": "Призрак",
            "last_name": "Тест",
            "role": "Призрак",
            "description": "Несуществующий сотрудник для теста",
            "order_priority": "0",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_team_member_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может обновлять данные сотрудников."""
    member = await create_member(db_session, "Защищённый", "Сотрудник")
    response = await client.put(
        f"/api/team/{member.id}",
        headers=auth_headers(client_token),
        data={
            "first_name": "Защищённый",
            "last_name": "Сотрудник",
            "role": "Взломщик",
            "description": "Попытка несанкционированного обновления",
            "order_priority": "0",
        },
    )
    assert response.status_code == 403


# ===========================================================================
# DELETE /api/team/{member_id}  (только Администратор)
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_team_member_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор удаляет сотрудника."""
    member = await create_member(db_session, "На", "Удаление")
    response = await client.delete(
        f"/api/team/{member.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Проверяем, что сотрудника больше нет
    get_response = await client.get(f"/api/team/{member.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_team_member_not_found(client: AsyncClient, admin_token: str):
    """Удаление несуществующего сотрудника → 404."""
    response = await client.delete(
        "/api/team/999999", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_team_member_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может удалять сотрудников."""
    member = await create_member(db_session, "Нельзя", "Удалить")
    response = await client.delete(
        f"/api/team/{member.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_team_member_no_auth(
    client: AsyncClient, db_session: AsyncSession
):
    """Без токена → 401."""
    member = await create_member(db_session, "Без", "Токена")
    response = await client.delete(f"/api/team/{member.id}")
    assert response.status_code == 401
