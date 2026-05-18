"""
Тесты: /api/users/
"""

import pytest
from common.models import User, UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers, make_token

# ---------------------------------------------------------------------------
# Фабрика пользователя
# ---------------------------------------------------------------------------


async def create_user(
    db: AsyncSession,
    tg_id: int,
    username: str = "user",
    role: UserRole = UserRole.CLIENT,
) -> User:
    u = User(tg_id=tg_id, username=username, first_name="Тест", role=role)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


# ===========================================================================
# GET /api/users/
# ===========================================================================


@pytest.mark.asyncio
async def test_get_all_users_as_admin(
    client: AsyncClient, admin_token: str, client_user: User
):
    """Администратор получает список всех пользователей."""
    response = await client.get("/api/users/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_all_users_contains_expected_fields(
    client: AsyncClient, admin_token: str, client_user: User
):
    """Каждый объект содержит обязательные поля схемы UsersRead."""
    response = await client.get("/api/users/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    for user in response.json():
        assert "id" in user
        assert "role" in user
        assert "tg_id" in user


@pytest.mark.asyncio
async def test_get_all_users_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь не может просматривать список пользователей."""
    response = await client.get("/api/users/", headers=auth_headers(client_token))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_all_users_no_auth(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/users/")
    assert response.status_code == 401


# ===========================================================================
# PATCH /api/users/{user_id}/role
# ===========================================================================


@pytest.mark.asyncio
async def test_promote_client_to_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор повышает CLIENT до ADMIN."""
    user = await create_user(db_session, tg_id=10000001, username="topromote")
    response = await client.patch(
        f"/api/users/{user.id}/role",
        headers=auth_headers(admin_token),
        json={"role": "ADMIN"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.ADMIN.value


@pytest.mark.asyncio
async def test_demote_admin_to_client(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор понижает другого ADMIN до CLIENT."""
    other_admin = await create_user(
        db_session, tg_id=10000002, username="otheradmin", role=UserRole.ADMIN
    )
    response = await client.patch(
        f"/api/users/{other_admin.id}/role",
        headers=auth_headers(admin_token),
        json={"role": "CLIENT"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.CLIENT.value


@pytest.mark.asyncio
async def test_update_role_keeps_other_fields(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Смена роли не затирает другие поля пользователя."""
    user = await create_user(db_session, tg_id=10000003, username="keepfields")
    response = await client.patch(
        f"/api/users/{user.id}/role",
        headers=auth_headers(admin_token),
        json={"role": "ADMIN"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "keepfields"
    assert body["tg_id"] == 10000003


@pytest.mark.asyncio
async def test_admin_cannot_demote_self(
    client: AsyncClient, admin_user: User, admin_token: str
):
    """Администратор не может снять права с себя — защита от потери доступа."""
    response = await client.patch(
        f"/api/users/{admin_user.id}/role",
        headers=auth_headers(admin_token),
        json={"role": "CLIENT"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_can_keep_own_admin_role(
    client: AsyncClient, admin_user: User, admin_token: str
):
    """Администратор может «переназначить» себе роль ADMIN — это не ошибка."""
    response = await client.patch(
        f"/api/users/{admin_user.id}/role",
        headers=auth_headers(admin_token),
        json={"role": "ADMIN"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.ADMIN.value


@pytest.mark.asyncio
async def test_update_role_invalid_value(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Неизвестная роль → 422."""
    user = await create_user(db_session, tg_id=10000004, username="badrole")
    response = await client.patch(
        f"/api/users/{user.id}/role",
        headers=auth_headers(admin_token),
        json={"role": "SUPERUSER"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_role_user_not_found(client: AsyncClient, admin_token: str):
    """Несуществующий пользователь → 404."""
    response = await client.patch(
        "/api/users/999999/role",
        headers=auth_headers(admin_token),
        json={"role": "ADMIN"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_role_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может менять роли."""
    user = await create_user(db_session, tg_id=10000005, username="targetrole")
    response = await client.patch(
        f"/api/users/{user.id}/role",
        headers=auth_headers(client_token),
        json={"role": "ADMIN"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_role_no_auth(client: AsyncClient, db_session: AsyncSession):
    """Без токена → 401."""
    user = await create_user(db_session, tg_id=10000006, username="noauthuser")
    response = await client.patch(
        f"/api/users/{user.id}/role",
        json={"role": "ADMIN"},
    )
    assert response.status_code == 401


# ===========================================================================
# DELETE /api/users/{user_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_delete_user_as_admin(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Администратор удаляет другого пользователя."""
    user = await create_user(db_session, tg_id=20000001, username="todelete")
    response = await client.delete(
        f"/api/users/{user.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_delete_user_actually_removes_from_db(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """После удаления пользователь пропадает из списка."""
    user = await create_user(db_session, tg_id=20000002, username="reallydelete")
    await client.delete(f"/api/users/{user.id}", headers=auth_headers(admin_token))

    list_response = await client.get("/api/users/", headers=auth_headers(admin_token))
    ids = [u["id"] for u in list_response.json()]
    assert user.id not in ids


@pytest.mark.asyncio
async def test_admin_cannot_delete_self(
    client: AsyncClient, admin_user: User, admin_token: str
):
    """Администратор не может удалить собственный аккаунт."""
    response = await client.delete(
        f"/api/users/{admin_user.id}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, admin_token: str):
    """Удаление несуществующего пользователя → 404."""
    response = await client.delete(
        "/api/users/999999", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_forbidden_for_client(
    client: AsyncClient, db_session: AsyncSession, client_token: str
):
    """Обычный пользователь не может удалять других пользователей."""
    other = await create_user(db_session, tg_id=20000003, username="othertodelete")
    response = await client.delete(
        f"/api/users/{other.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_no_auth(client: AsyncClient, db_session: AsyncSession):
    """Без токена → 401."""
    user = await create_user(db_session, tg_id=20000004, username="noauthdelete")
    response = await client.delete(f"/api/users/{user.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_deleted_user_token_becomes_invalid(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    """Токен удалённого пользователя перестаёт работать."""
    user = await create_user(db_session, tg_id=20000005, username="ghostuser")
    user_token = make_token(user)

    # Сначала токен рабочий
    r1 = await client.get("/api/auth/verify-admin", headers=auth_headers(user_token))
    # Пользователь не админ, но токен валиден → 403, не 401
    assert r1.status_code == 403

    # Удаляем пользователя
    await client.delete(f"/api/users/{user.id}", headers=auth_headers(admin_token))

    # Теперь токен невалиден → 401
    r2 = await client.get("/api/auth/verify-admin", headers=auth_headers(user_token))
    assert r2.status_code == 401
