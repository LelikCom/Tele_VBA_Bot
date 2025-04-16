"""
logger.py

Логика логирования диалога:
- log_question: сохраняет сообщение пользователя
- log_answer: сохраняет ответ бота
"""

import logging
from datetime import datetime, timedelta
import pytz
from dateutil import parser

from db.dialog_log import (
    get_last_session,
    start_new_session,
    insert_question,
    insert_answer,
    SESSION_TIMEOUT_MINUTES
)


moscow = pytz.timezone("Europe/Moscow")


async def get_or_create_session(user_id: int) -> tuple[str, int]:
    """
    Проверяет активную сессию пользователя. Возвращает session_id и следующий step.
    Если прошло более SESSION_TIMEOUT_MINUTES — создаёт новую сессию.

    Args:
        user_id (int): ID пользователя.

    Returns:
        tuple[str, int]: session_id и номер следующего шага.
    """
    now_msk = datetime.now(moscow).replace(tzinfo=None)
    last_session = get_last_session(user_id)

    if last_session:
        session_id, last_step, last_time = last_session

        if isinstance(last_time, str):
            last_time = parser.parse(last_time)
        if isinstance(last_time, datetime):
            last_time = last_time.replace(tzinfo=None)

        if (now_msk - last_time) < timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            return session_id, last_step + 1

    return start_new_session(), 1


async def log_question(
    user_id: int,
    username: str,
    message_id: int,
    message_text: str,
    point: str
) -> None:
    """
    Логирует сообщение пользователя.

    Args:
        user_id (int): Telegram ID.
        username (str): username Telegram.
        message_id (int): ID сообщения.
        message_text (str): Текст.
        point (str): Точка сценария.
    """
    session_id, step = await get_or_create_session(user_id)
    now_msk = datetime.now(moscow).replace(tzinfo=None)
    insert_question(session_id, step, user_id, username, message_id, message_text, point, now_msk)


async def log_answer(
    user_id: int,
    message_id: int,
    answer_text: str
) -> None:
    """
    Логирует ответ бота к последнему шагу.

    Args:
        user_id (int): Telegram ID.
        message_id (int): ID сообщения ответа.
        answer_text (str): Ответ бота.
    """
    try:
        now_msk = datetime.now(moscow).replace(tzinfo=None)
        insert_answer(user_id, message_id, answer_text, now_msk)
    except Exception as e:
        logging.error(f"[log_answer] Ошибка при вставке ответа: {e}")
