import logging
from typing import Optional, List, Tuple
from db.connection import get_db_connection

"""
Модуль для работы с таблицей пользователей User_Contacts_VBA в базе данных PostgreSQL.
Включает функции для получения, обновления и добавления пользователей, а также работы с ролями.
"""


async def get_user_role_by_id(user_id: int) -> str:
    """
    Асинхронная функция для получения роли пользователя.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        str: Роль пользователя или 'noauth', если не найден.
    """
    query = "SELECT role FROM User_Contacts_VBA WHERE user_id = $1"
    try:
        async with get_db_connection() as conn:
            record = await conn.fetchrow(query, user_id)
            return record['role'] if record else 'noauth'
    except Exception as e:
        logging.error(f"Ошибка при получении роли пользователя {user_id}: {e}")
        return 'noauth'


async def get_user_role(user_id: int) -> str:
    """
    Получает роль пользователя по его идентификатору.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        str: Роль пользователя, либо "noauth", если не найден или при ошибке.
    """
    query = "SELECT role FROM User_Contacts_VBA WHERE user_id = $1"
    try:
        async with get_db_connection() as conn:
            record = await conn.fetchrow(query, user_id)
            return record['role'] if record else "noauth"
    except Exception as e:
        logging.error(f"Ошибка при получении роли пользователя {user_id}: {e}")
        return "noauth"


async def get_all_user_roles() -> List[Tuple[int, str]]:
    """
    Возвращает список всех пользователей и их ролей.

    Returns:
        List[Tuple[int, str]]: Список кортежей (user_id, role).
    """
    query = "SELECT user_id, role FROM User_Contacts_VBA"
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query)
            return [(r['user_id'], r['role']) for r in records]
    except Exception as e:
        logging.error(f"Ошибка при получении всех ролей: {e}")
        return []


async def get_all_roles_from_db() -> List[str]:
    """
    Возвращает уникальные роли пользователей из таблицы.

    Returns:
        List[str]: Список уникальных ролей.
    """
    query = "SELECT DISTINCT role FROM User_Contacts_VBA WHERE role IS NOT NULL"
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query)
            return [r['role'] for r in records]
    except Exception as e:
        logging.error(f"Ошибка при получении списка ролей: {e}")
        return []


async def fetch_users_by_role(role: str, limit: Optional[int] = None, offset: int = 0) -> List[Tuple[int, str, str]]:
    """
    Возвращает список пользователей с указанной ролью.

    Args:
        role (str): Роль пользователя.
        limit (Optional[int]): Количество записей для ограничения выборки.
        offset (int): Смещение для пагинации.

    Returns:
        List[Tuple[int, str, str]]: Список кортежей (user_id, username, phone_number).
    """
    base_query = "SELECT user_id, username, phone_number FROM User_Contacts_VBA WHERE role = $1 ORDER BY user_id"
    try:
        async with get_db_connection() as conn:
            if limit is not None:
                records = await conn.fetch(base_query + " LIMIT $2 OFFSET $3", role, limit, offset)
            else:
                records = await conn.fetch(base_query, role)
            return [(r['user_id'], r['username'], r['phone_number']) for r in records]
    except Exception as e:
        logging.error(f"Ошибка при получении пользователей с ролью '{role}': {e}")
        return []


async def get_users_by_role(role: str) -> List[int]:
    """
    Возвращает список user_id для пользователей с указанной ролью.

    Args:
        role (str): Название роли.

    Returns:
        List[int]: Список Telegram ID пользователей.
    """
    query = "SELECT user_id FROM User_Contacts_VBA WHERE role = $1"
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query, role)
            return [r['user_id'] for r in records]
    except Exception as e:
        logging.error(f"Ошибка при получении пользователей по роли '{role}': {e}")
        return []


async def fetch_user_by_user_id(user_id: int) -> Optional[Tuple[int, str, str, str, str, str]]:
    """
    Получает информацию о пользователе по его ID.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        Optional[Tuple]: Кортеж (user_id, username, phone_number, timestamp, comment, role).
    """
    query = (
        "SELECT user_id, username, phone_number "
        "FROM User_Contacts_VBA WHERE user_id = $1 LIMIT 1"
    )
    print(query)
    logging.error(f"Запрос {query}")
    try:
        async with get_db_connection() as conn:
            record = await conn.fetchrow(query, user_id)
            return tuple(record) if record else None
    except Exception as e:
        logging.error(f"Ошибка при получении пользователя {user_id}: {e}")
        return None


async def fetch_all_users() -> List[Tuple]:
    """
    Возвращает список всех пользователей.

    Returns:
        List[Tuple]: Кортежи (user_id, username, phone_number, timestamp, comment, role).
    """
    query = (
        "SELECT user_id, username, phone_number, timestamp, comment, role "
        "FROM User_Contacts_VBA ORDER BY timestamp ASC"
    )
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query)
            return [tuple(r) for r in records]
    except Exception as e:
        logging.error(f"Ошибка при извлечении пользователей: {e}")
        return []


async def save_user(user_id: int, username: Optional[str] = None, phone_number: Optional[str] = None) -> None:
    """
    Добавляет нового пользователя или обновляет его имя и номер телефона.

    Args:
        user_id (int): Telegram ID пользователя.
        username (Optional[str]): Имя пользователя.
        phone_number (Optional[str]): Телефон, если указан.

    Note:
        Роль пользователя не обновляется — используется отдельная функция.
    """
    query = (
        "INSERT INTO User_Contacts_VBA (user_id, username, phone_number) "
        "VALUES ($1, $2, $3) "
        "ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username, "
        "phone_number = CASE WHEN EXCLUDED.phone_number IS NULL THEN User_Contacts_VBA.phone_number ELSE EXCLUDED.phone_number END"
    )
    try:
        async with get_db_connection() as conn:
            await conn.execute(query, user_id, username, phone_number)
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя {user_id}: {e}")


async def update_user_role(user_id: int, new_role: str, phone_number: Optional[str] = None) -> bool:
    """
    Обновляет роль пользователя и, при необходимости, номер телефона.

    Args:
        user_id (int): Telegram ID пользователя.
        new_role (str): Новая роль.
        phone_number (Optional[str]): Новый номер телефона (если нужно).

    Returns:
        bool: True, если было обновлено >=1 строк, иначе False.
    """
    if phone_number is None:
        query = "UPDATE User_Contacts_VBA SET role = $1 WHERE user_id = $2"
        params = (new_role, user_id)
    else:
        query = "UPDATE User_Contacts_VBA SET role = $1, phone_number = $2 WHERE user_id = $3"
        params = (new_role, phone_number, user_id)
    try:
        async with get_db_connection() as conn:
            status = await conn.execute(query, *params)
            updated = int(status.split()[-1])
            return updated > 0
    except Exception as e:
        logging.error(f"Ошибка обновления роли пользователя {user_id}: {e}")
        return False


async def update_comment(user_id: int, comment: str) -> None:
    """
    Обновляет комментарий пользователя.

    Args:
        user_id (int): Telegram ID пользователя.
        comment (str): Новый комментарий.
    """
    query = "UPDATE User_Contacts_VBA SET comment = $1 WHERE user_id = $2"
    try:
        async with get_db_connection() as conn:
            await conn.execute(query, comment, user_id)
    except Exception as e:
        logging.error(f"Ошибка при обновлении комментария пользователя {user_id}: {e}")
