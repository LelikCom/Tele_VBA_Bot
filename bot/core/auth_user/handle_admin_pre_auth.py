"""
handle_admin_pre_auth.py

Обработка подтверждения и отклонения заявок на авторизацию администратором.
"""

import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.users import fetch_user_by_user_id

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
logger = logging.getLogger(__name__)
AVAILABLE_ROLES = ["auth", "noauth", "admin", "rejected", "preauth"]


async def handle_pre_auth_user_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка выбора пользователя с ролью `preauth` из списка.

    Args:
        update (Update): Callback-запрос от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.
    """
    query = update.callback_query
    await query.answer()

    try:
        _, _, role, user_id_str = query.data.split("_", 3)

        if role != "preauth":
            await query.edit_message_text("❌ Эта функция доступна только для preauth.")
            return

        user_data = await fetch_user_by_user_id(int(user_id_str))
        if not user_data:
            await query.edit_message_text("❌ Пользователь не найден.")
            return

        tg_id, username, phone = user_data
        text = (
            f"📄 Заявка пользователя:\n"
            f"• Пользователь: @{username or 'без username'}\n"
            f"• ID: {tg_id}\n"
            f"• Номер: {phone}"
        )

        buttons = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"auth_approve_{tg_id}_{phone}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"auth_reject_{tg_id}_{phone}")
            ],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_roles")]
        ]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error("Ошибка выбора пользователя preauth: %s", e, exc_info=True)
        await query.edit_message_text("❌ Ошибка обработки заявки.")
