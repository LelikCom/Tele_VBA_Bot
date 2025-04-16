"""
dialog_log.py

Модуль для работы с логами диалога (таблица dialog_log):
- Вставка вопросов и ответов
- Получение последней сессии
- Генерация новой сессии
"""

import uuid
import logging
from datetime import datetime
import pytz
from db.connection import connect_db

logger = logging.getLogger(__name__)
moscow = pytz.timezone("Europe/Moscow")
SESSION_TIMEOUT_MINUTES = 15


def get_last_session(user_id: int):
    """
    Возвращает последнюю сессию пользователя.

    Args:
        user_id (int): ID пользователя.

    Returns:
        tuple | None: (session_id, step, time_question) или None при ошибке.
    """
    query = """
        SELECT session_id, step, time_question
        FROM dialog_log
        WHERE user_id = %s
        ORDER BY time_question DESC
        LIMIT 1
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id,))
                return cur.fetchone()
    except Exception as e:
        logger.error("Ошибка в get_last_session: %s", e)
        return None


def start_new_session() -> str:
    """
    Генерирует новый UUID для сессии.

    Returns:
        str: UUID строки сессии.
    """
    return str(uuid.uuid4())


def insert_question(
    session_id: str,
    step: int,
    user_id: int,
    username: str,
    message_id: int,
    question: str,
    point: str,
    time_question: datetime
) -> None:
    """
    Сохраняет сообщение пользователя в таблицу dialog_log.

    Args:
        session_id (str): Идентификатор сессии.
        step (int): Шаг в сессии.
        user_id (int): Telegram ID пользователя.
        username (str): Username пользователя.
        message_id (int): ID сообщения.
        question (str): Текст вопроса.
        point (str): Точка сценария (например, "CONTACT").
        time_question (datetime): Время вопроса.
    """
    query = """
        INSERT INTO dialog_log (
            session_id, step, user_id, username,
            id_question, question, time_question, point
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    session_id, step, user_id, username,
                    message_id, question, time_question, point
                ))
                conn.commit()
    except Exception as e:
        logger.error("Ошибка в insert_question: %s", e)


def insert_answer(
    user_id: int,
    message_id: int,
    answer: str,
    time_answer: datetime
) -> None:
    """
    Обновляет последнюю строку пользователя в dialog_log, добавляя ответ.

    Args:
        user_id (int): Telegram ID пользователя.
        message_id (int): ID ответа бота.
        answer (str): Текст ответа.
        time_answer (datetime): Время ответа.
    """
    query = """
        UPDATE dialog_log
        SET id_answer = %s, answer = %s, time_answer = %s
        WHERE user_id = %s AND id_answer IS NULL
        AND step = (
            SELECT MAX(step)
            FROM dialog_log
            WHERE user_id = %s AND id_answer IS NULL
        )
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    message_id, answer, time_answer,
                    user_id, user_id
                ))
                conn.commit()
    except Exception as e:
        logger.error("Ошибка в insert_answer: %s", e)
