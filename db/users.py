"""
users.py

Модуль для работы с таблицей пользователей User_Contacts_VBA в базе данных PostgreSQL.
Включает функции для получения, обновления и добавления пользователей, а также работы с ролями.
"""

import asyncio
import logging
from typing import Optional
from db.connection import connect_db


async def get_user_role_by_id(user_id: int) -> str:
    """
    Асинхронная обертка для получения роли пользователя.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        str: Роль пользователя.
    """
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, get_user_role, user_id)
    except Exception as e:
        logging.error(f"Ошибка в get_user_role_by_id для user_id={user_id}: {e}")
        return "noauth"


def get_user_role(user_id: int) -> str:
    """
    Получает роль пользователя по его идентификатору.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        str: Роль пользователя, либо "noauth", если не найден или возникла ошибка.
    """
    query = "SELECT role FROM User_Contacts_VBA WHERE user_id = %s"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                result = cur.fetchone()
                return result[0] if result else "noauth"
    except Exception as e:
        logging.error(f"Ошибка при получении роли пользователя {user_id}: {e}")
        return "noauth"


def get_all_user_roles() -> list[tuple[int, str]]:
    """
    Возвращает список всех пользователей и их ролей.

    Returns:
        list[tuple[int, str]]: Список кортежей (user_id, role).
    """
    query = "SELECT user_id, role FROM User_Contacts_VBA"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при получении всех ролей: {e}")
        return []


def get_all_roles_from_db() -> list[str]:
    """
    Возвращает уникальные роли пользователей из таблицы.

    Returns:
        list[str]: Список уникальных ролей.
    """
    query = "SELECT DISTINCT role FROM User_Contacts_VBA WHERE role IS NOT NULL"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка при получении списка ролей: {e}")
        return []


def fetch_users_by_role(role: str, limit: int = None, offset: int = 0) -> list[tuple[int, str, str]]:
    """
    Возвращает список пользователей с указанной ролью (user_id, username, phone_number).

    Args:
        role (str): Роль пользователя (например, 'auth', 'admin').
        limit (int, optional): Кол-во записей для ограничения выборки.
        offset (int, optional): Смещение для пагинации.

    Returns:
        list[tuple[int, str, str]]: Список кортежей с user_id, username, phone_number.
    """
    query = """
    SELECT user_id, username, phone_number FROM User_Contacts_VBA
    WHERE role = %s
    ORDER BY user_id
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                if limit:
                    query += " LIMIT %s OFFSET %s"
                    cur.execute(query, (role, limit, offset))
                else:
                    cur.execute(query, (role,))
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при получении пользователей с ролью '{role}': {e}")
        return []


def get_users_by_role(role: str) -> list[int]:
    """
    Возвращает список user_id для пользователей с указанной ролью.

    Args:
        role (str): Название роли.

    Returns:
        list[int]: Список Telegram ID пользователей.
    """
    query = "SELECT user_id FROM User_Contacts_VBA WHERE role = %s"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (role,))
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка при получении пользователей по роли '{role}': {e}")
        return []


def fetch_user_by_user_id(user_id: int) -> Optional[tuple]:
    """
    Получает информацию о пользователе по его ID.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        Optional[tuple]: Кортеж с данными пользователя или None.
    """
    query = """
    SELECT user_id, username, phone_number
    FROM User_Contacts_VBA
    WHERE user_id = %s
    LIMIT 1
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                return cur.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при получении пользователя {user_id}: {e}")
        return None


def fetch_all_users() -> list[tuple]:
    """
    Возвращает список всех пользователей.

    Returns:
        list[tuple]: Кортежи (user_id, username, phone_number, timestamp, comment, role)
    """
    query = """
    SELECT user_id, username, phone_number, timestamp, comment, role
    FROM User_Contacts_VBA
    ORDER BY timestamp ASC
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при извлечении пользователей: {e}")
        return []


def save_user(user_id: int, username: Optional[str] = None, phone_number: Optional[str] = None) -> None:
    """
    Добавляет нового пользователя или обновляет его имя и номер телефона.

    Args:
        user_id (int): Telegram ID пользователя.
        username (Optional[str]): Имя пользователя.
        phone_number (Optional[str]): Телефон, если указан.

    Note:
        Роль пользователя не обновляется — используется отдельная функция.
    """
    query = """
    INSERT INTO User_Contacts_VBA (user_id, username, phone_number)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET username = EXCLUDED.username,
                  phone_number = CASE 
                                   WHEN EXCLUDED.phone_number IS NULL 
                                   THEN User_Contacts_VBA.phone_number 
                                   ELSE EXCLUDED.phone_number 
                                 END;
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, username, phone_number))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя {user_id}: {e}")


async def update_user_role(user_id: int, new_role: str, phone_number: str = None) -> bool:
    """
    Обновляет роль пользователя в базе данных, а также обновляет номер телефона, если он передан.
    Возвращает True при успешном обновлении, False при ошибке.
    """
    query = """
        UPDATE public.user_contacts_vba
        SET role = %s, phone_number = %s
        WHERE user_id = %s
    """

    if phone_number is None:
        query = """
            UPDATE public.user_contacts_vba
            SET role = %s
            WHERE user_id = %s
        """
        params = (new_role, user_id)
    else:
        params = (new_role, phone_number, user_id)

    print(f"🔲 Выполняем запрос с параметрами: {params}")

    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()

                if cur.rowcount > 0:
                    print(f"🔲 Успешно обновлены данные для пользователя {user_id}.")
                    return True
                else:
                    print(f"⚠ Для пользователя {user_id} не было обновлено ни одной строки.")
                    return False

    except Exception as e:
        print(f"❌ Ошибка обновления данных: {e}")
        return False


def update_comment(user_id: int, comment: str) -> None:
    """
    Обновляет комментарий пользователя.

    Args:
        user_id (int): Telegram ID пользователя.
        comment (str): Новый комментарий.
    """
    query = "UPDATE User_Contacts_VBA SET comment = %s WHERE user_id = %s"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (comment, user_id))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при обновлении комментария пользователя {user_id}: {e}")
