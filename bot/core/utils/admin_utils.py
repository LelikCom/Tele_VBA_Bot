"""
admin_utils.py

Вспомогательные функции для администраторов Telegram-бота:
- Проверка прав доступа
- Очистка состояний
- Получение текущего времени по МСК
"""
import logging
import pytz
from typing import List
from datetime import datetime, timedelta, timezone
from telegram.ext import ContextTypes

from db.users import get_users_by_role

# Устанавливаем московский часовой пояс
MSK = pytz.timezone('Europe/Moscow')


# Асинхронная функция для получения текущего времени в МСК
async def get_now_msk() -> datetime:
    """
    Возвращает текущую дату и время в часовом поясе МСК.

    Returns:
        datetime: Текущее время в зоне Europe/Moscow.
    """
    return datetime.now(MSK)


# Асинхронная функция для очистки состояния пользователя
async def reset_all_user_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Очищает состояние пользователя в user_data.

    Args:
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram-бота.
    """
    context.user_data.clear()


async def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором.

    Args:
        user_id (int): Telegram user_id.

    Returns:
        bool: True, если пользователь — админ, иначе False.
    """
    try:
        admins: List[int] = await get_users_by_role("admin")
        return user_id in admins
    except Exception as e:
        logging.error(f"Ошибка при проверке прав администратора: {e}")
        return False

