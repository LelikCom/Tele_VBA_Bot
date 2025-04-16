"""
users.py

Обработка административных запросов по пользователям:
- Список всех пользователей
- Фильтрация по ролям
"""

from telegram import Update
from telegram.ext import ContextTypes
from bot.core.handlers_for_all.other_handler import get_all_users


async def handle_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    return await get_all_users(update, context)
