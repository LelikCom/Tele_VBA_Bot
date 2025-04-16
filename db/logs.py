"""
logs.py

Модуль для работы с логами взаимодействия пользователя и бота.
Использует таблицу dialog_log для хранения и анализа данных.
"""

import logging
from typing import Optional, List
from db.connection import connect_db


def get_bot_messages_for_user(user_id: int) -> List[int]:
    """
    Возвращает список идентификаторов сообщений (id_answer), которые бот отправил пользователю.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        List[int]: Список ID сообщений от бота (id_answer).
    """
    query = """
        SELECT id_answer FROM dialog_log
        WHERE user_id = %s AND id_answer IS NOT NULL
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка при получении сообщений бота для user_id={user_id}: {e}")
        return []


def delete_bot_messages_for_user(user_id: int) -> None:
    """
    Удаляет записи из dialog_log, содержащие id сообщений от бота для указанного пользователя.

    Args:
        user_id (int): Telegram ID пользователя.
    """
    query = """
        DELETE FROM dialog_log
        WHERE user_id = %s AND id_answer IS NOT NULL
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                conn.commit()
        logging.debug(f"Удалены сообщения бота для пользователя {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщений бота для user_id={user_id}: {e}")


def get_average_response_time(since: Optional[str] = None) -> Optional[float]:
    """
    Вычисляет среднее время ответа бота на сообщения пользователей.

    Args:
        since (Optional[str]): Дата/время начала периода в формате 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        Optional[float]: Среднее время ответа в секундах, или None при отсутствии данных.
    """
    if since:
        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (time_answer - time_question)))
            FROM dialog_log
            WHERE time_answer IS NOT NULL
              AND time_question IS NOT NULL
              AND time_answer > %s
        """
        params = (since,)
    else:
        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (time_answer - time_question)))
            FROM dialog_log
            WHERE time_answer IS NOT NULL AND time_question IS NOT NULL
        """
        params = ()

    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                return result[0] if result and result[0] is not None else None
    except Exception as e:
        logging.error(f"Ошибка при вычислении среднего времени ответа: {e}")
        return None
