"""
panel.py

Панель администратора Telegram-бота.
Отображает основное меню с кнопками.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.core.keyboards.admin_panel import get_admin_panel_keyboard


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отображает главное меню админ-панели.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст пользователя.
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="🔧 Админ-панель:",
        reply_markup=get_admin_panel_keyboard()
    )
