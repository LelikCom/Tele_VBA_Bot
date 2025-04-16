"""
feedback.py

Модуль для работы с таблицей обратной связи `feedback` в базе данных PostgreSQL.
Позволяет добавлять, извлекать, помечать прочитанными отзывы, а также загружать вложения.
"""

import logging
from typing import Optional, List, Tuple
from db.connection import connect_db


def add_feedback(
    user_id: int,
    theme: str,
    message: str,
    attachment: Optional[str] = None,
    attachment_type: Optional[str] = None,
) -> None:
    """
    Добавляет новую запись обратной связи в базу данных.

    Args:
        user_id (int): Telegram ID пользователя.
        theme (str): Тема обращения.
        message (str): Текст сообщения (ограничен 5000 символами).
        attachment (Optional[str]): Имя/путь вложенного файла (если есть).
        attachment_type (Optional[str]): Тип вложения (например, "photo", "document").

    Raises:
        Exception: Если произошла ошибка при вставке записи.
    """
    message = message[:5000]  # Безопасный лимит по длине текста

    query = """
        INSERT INTO feedback (user_id, theme, message, is_read, attachment, attachment_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (user_id, theme, message, False, attachment, attachment_type)

    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
        logging.debug(f"[DB] Обратная связь от {user_id} успешно добавлена.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении обратной связи от {user_id}: {e}")
        raise


def fetch_unread_feedback(limit: int = 5, offset: int = 0) -> List[Tuple]:
    """
    Извлекает список непрочитанных отзывов.

    Args:
        limit (int): Максимальное количество записей (по умолчанию 5).
        offset (int): Смещение (для пагинации).

    Returns:
        List[Tuple]: Список отзывов как кортежей.
    """
    query = """
        SELECT id, user_id, theme, message, attachment, attachment_type, created_at
        FROM feedback
        WHERE is_read = false
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit, offset))
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при извлечении непрочитанных отзывов: {e}")
        return []


def mark_feedback_as_read(feedback_id: int) -> None:
    """
    Помечает отзыв как прочитанный.

    Args:
        feedback_id (int): Идентификатор записи обратной связи.
    """
    query = "UPDATE feedback SET is_read = true WHERE id = %s"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (feedback_id,))
                conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при обновлении статуса отзыва {feedback_id}: {e}")


def fetch_feedback_by_id(feedback_id: int) -> Optional[Tuple]:
    """
    Извлекает один отзыв по его идентификатору.

    Args:
        feedback_id (int): Идентификатор отзыва.

    Returns:
        Optional[Tuple]: Кортеж с данными отзыва или None.
    """
    query = """
        SELECT id, user_id, theme, message, attachment, attachment_type, created_at
        FROM feedback
        WHERE id = %s
        LIMIT 1
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (feedback_id,))
                return cur.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при получении отзыва с ID={feedback_id}: {e}")
        return None
