import logging
from typing import Optional, List
from db.connection import get_db_connection
import pytz
from datetime import datetime

"""
Модуль для работы с логами взаимодействия пользователя и бота.
Использует таблицу dialog_log для хранения и анализа данных.
"""

# Устанавливаем московский часовой пояс
MSK = pytz.timezone('Europe/Moscow')
UTC = pytz.utc  # Временная зона UTC


async def get_bot_messages_for_user(user_id: int) -> List[int]:
    """
    Возвращает список идентификаторов сообщений (id_answer), которые бот отправил пользователю.

    Args:
        user_id (int): Telegram ID пользователя.

    Returns:
        List[int]: Список ID сообщений от бота (id_answer).
    """
    query = """
        SELECT id_answer FROM dialog_log
        WHERE user_id = $1 AND id_answer IS NOT NULL
    """
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query, user_id)
            return [r['id_answer'] for r in records]
    except Exception as e:
        logging.error(f"Ошибка при получении сообщений бота для user_id={user_id}: {e}")
        return []


async def delete_bot_messages_for_user(user_id: int) -> None:
    """
    Удаляет записи из dialog_log, содержащие id сообщений от бота для указанного пользователя.

    Args:
        user_id (int): Telegram ID пользователя.
    """
    query = """
        DELETE FROM dialog_log
        WHERE user_id = $1 AND id_answer IS NOT NULL
    """
    try:
        async with get_db_connection() as conn:
            await conn.execute(query, user_id)
        logging.debug(f"Удалены сообщения бота для пользователя {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщений бота для user_id={user_id}: {e}")


async def get_average_response_time(since: Optional[str] = None) -> Optional[float]:
    """
    Вычисляет среднее время ответа бота на сообщения пользователей.

    Args:
        since (Optional[str]): Дата/время начала периода в формате 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        Optional[float]: Среднее время ответа в секундах, или None при отсутствии данных.
    """
    if since:
        logging.info(f"Получена дата 'since': {since}")

        if isinstance(since, str):
            # Если since — строка, преобразуем в datetime
            since_dt = datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
            logging.info(f"Преобразована строка в datetime: {since_dt}")
        elif isinstance(since, datetime):
            # Если since — уже объект datetime, просто используем его
            since_dt = since
            logging.info(f"Используется уже объект datetime: {since_dt}")
        else:
            raise ValueError(f"Неизвестный тип аргумента since: {type(since)}")

        # Проверка, является ли datetime "naive"
        if since_dt.tzinfo is None:
            # Если "naive", локализуем в МСК
            logging.info(f"Дата 'since_dt' не содержит информации о временной зоне, локализуем в МСК: {since_dt}")
            since_dt = MSK.localize(since_dt)
        else:
            # Если уже "aware", просто меняем временную зону на МСК
            logging.info(f"Дата 'since_dt' уже содержит информацию о временной зоне, меняем на МСК: {since_dt}")
            since_dt = since_dt.astimezone(MSK)

        # Приводим дату к naive datetime в МСК
        since_dt = since_dt.replace(tzinfo=None)
        logging.info(f"Дата 'since_dt' в МСК (naive): {since_dt}")

        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (time_answer - time_question)))
            FROM dialog_log
            WHERE time_answer IS NOT NULL
              AND time_question IS NOT NULL
              AND time_answer > $1
        """
        params = (since_dt,)
    else:
        query = """
            SELECT AVG(EXTRACT(EPOCH FROM (time_answer - time_question)))
            FROM dialog_log
            WHERE time_answer IS NOT NULL AND time_question IS NOT NULL
        """
        params = ()

    try:
        async with get_db_connection() as conn:
            result = await conn.fetchrow(query, *params)
            logging.info(f"Результат запроса: {result}")
            return result[0] if result and result[0] is not None else None
    except Exception as e:
        logging.error(f"Ошибка при вычислении среднего времени ответа: {e}")
        return None
