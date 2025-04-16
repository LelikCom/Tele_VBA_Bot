"""
handle_auth_callback.py

Обрабатывает действия администратора по подтверждению или отклонению заявок пользователей.
"""

import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.users import update_user_role
from bot.core.keyboards.main_menu import get_main_menu_keyboard

logger = logging.getLogger(__name__)
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))


async def handle_auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает callback-кнопки подтверждения или отклонения заявки.

    Args:
        update (Update): Объект Telegram-обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.

    Returns:
        None
    """
    query = update.callback_query
    await query.answer()

    try:
        logger.info("Обработка callback: %s", query.data)

        _, action, user_id_str, phone = query.data.split("_", 3)
        user_id = int(user_id_str)

        if action == "approve":
            result = await _approve_user(update, context, user_id, phone)
        elif action == "reject":
            result = await _reject_user(update, context, user_id, phone)
        else:
            raise ValueError(f"Неизвестное действие: {action}")

        if not result:
            raise RuntimeError("Не удалось обновить роль пользователя.")

    except ValueError as e:
        logger.error("Ошибка формата данных: %s", e)
        await query.edit_message_text("⚠ Ошибка: некорректный формат запроса")
    except Exception as e:
        logger.error("Критическая ошибка: %s", e, exc_info=True)
        await query.edit_message_text("⚠ Произошла системная ошибка")
        await _notify_admin_about_error(context, user_id, e)


async def _approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, phone: str) -> bool:
    """
    Подтверждает заявку пользователя и уведомляет его.

    Args:
        update (Update): Объект Telegram-обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        user_id (int): ID пользователя.
        phone (str): Телефон пользователя.

    Returns:
        bool: True, если всё успешно.
    """
    success = await update_user_role(user_id, "auth", phone)
    if not success:
        return False

    await update.callback_query.edit_message_text(
        f"✅ Доступ предоставлен пользователю: `{user_id}` | 📞 `{phone}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Твоя заявка одобрена! Добро пожаловать!",
            reply_markup=get_main_menu_keyboard("auth")
        )
    except Exception as e:
        logger.warning("Не удалось отправить сообщение пользователю: %s", e)

    return True


async def _reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, phone: str) -> bool:
    """
    Отклоняет заявку пользователя и уведомляет его.

    Args:
        update (Update): Объект Telegram-обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        user_id (int): ID пользователя.
        phone (str): Телефон пользователя.

    Returns:
        bool: True, если отклонение прошло успешно.
    """
    success = await update_user_role(user_id, "rejected", phone)
    if not success:
        return False

    await update.callback_query.edit_message_text(
        f"🚫 Доступ отклонён для пользователя: `{user_id}` | 📞 `{phone}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Ваша заявка была отклонена.\nЕсли вы считаете это ошибкой — обратитесь к администратору."
        )
    except Exception as e:
        logger.warning("Не удалось отправить сообщение пользователю: %s", e)

    return True


async def _notify_admin_about_error(context: ContextTypes.DEFAULT_TYPE, user_id: int, error: Exception) -> None:
    """
    Уведомляет администратора о критической ошибке при обработке заявки.

    Args:
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        user_id (int): ID пользователя.
        error (Exception): Ошибка для отправки администратору.

    Returns:
        None
    """
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID не задан — уведомление не отправлено.")
        return

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"⚠️ Ошибка при обработке заявки от пользователя {user_id}:\n\n<code>{error}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error("Не удалось отправить сообщение администратору: %s", e)
