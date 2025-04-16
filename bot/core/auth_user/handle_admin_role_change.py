"""
handle_admin_role_change.py

Обработка изменения роли пользователя администратором:
- выбор новой роли
- подтверждение смены
- применение новой роли
"""

import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.users import fetch_user_by_user_id, get_user_role, update_user_role
from bot.core.auth_user.utils import get_available_roles

AVAILABLE_ROLES = get_available_roles()


logger = logging.getLogger(__name__)
AVAILABLE_ROLES = get_available_roles()


async def handle_user_role_change_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает выбор роли для смены пользователю.

    Args:
        update (Update): Объект CallbackQuery.
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.
    """
    query = update.callback_query
    await query.answer()

    try:
        parts = query.data.split("_")
        if len(parts) < 4:
            raise ValueError("Неверный формат callback_data")

        current_role = "_".join(parts[2:-1])
        user_id = int(parts[-1])

        if current_role == "preauth":
            await query.edit_message_text("❌ Пользователь ещё не подтверждён.")
            return

        user = fetch_user_by_user_id(user_id)
        if not user:
            await query.edit_message_text("❌ Пользователь не найден.")
            return

        user_id, username, phone = user

        text = (
            f"🧾 <b>Пользователь:</b>\n"
            f"• @{username or 'без username'}\n"
            f"• <b>ID:</b> {user_id}\n"
            f"• <b>Телефон:</b> {phone}\n"
            f"• <b>Текущая роль:</b> <code>{current_role}</code>\n\n"
            f"<b>Выберите новую роль:</b>"
        )

        keyboard = [
            [InlineKeyboardButton(f"🔁 {new_role}", callback_data=f"change_role_{user_id}_{new_role}")]
            for new_role in AVAILABLE_ROLES if new_role != current_role
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_roles")])

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error("Ошибка в handle_user_role_change_request: %s", e, exc_info=True)
        await query.edit_message_text("⚠ Ошибка обработки запроса.")


async def handle_role_change_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Подтверждение смены роли: показывает финальное подтверждение с кнопкой.

    Args:
        update (Update): Объект CallbackQuery.
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.
    """
    query = update.callback_query
    await query.answer()

    try:
        _, _, user_id_str, new_role = query.data.split("_", 3)
        user_id = int(user_id_str)

        user = fetch_user_by_user_id(user_id)
        if not user:
            await query.edit_message_text("❌ Пользователь не найден.")
            return

        user_id, username, phone = user
        current_role = get_user_role(user_id)

        text = (
            f"⚠ Вы уверены, что хотите изменить роль пользователя @{username or 'без username'} "
            f"с <code>{current_role}</code> на <code>{new_role}</code>?\n\n"
            f"Номер: <code>{phone}</code>"
        )

        keyboard = [
            [InlineKeyboardButton("✅ Да, изменить", callback_data=f"confirm_change_{user_id}_{new_role}")],
            [InlineKeyboardButton("❌ Отменить", callback_data="back_to_roles")],
        ]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error("Ошибка в handle_role_change_confirmation: %s", e, exc_info=True)
        await query.edit_message_text("⚠ Произошла ошибка.")


async def handle_confirm_role_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Применяет новую роль пользователю.

    Args:
        update (Update): Объект CallbackQuery.
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.
    """
    query = update.callback_query
    await query.answer()

    try:
        _, _, user_id_str, new_role = query.data.split("_", 3)
        user_id = int(user_id_str)

        success = await update_user_role(user_id=user_id, new_role=new_role)

        if success:
            await query.edit_message_text(
                text=f"✅ Роль пользователя <code>{user_id}</code> успешно обновлена на <code>{new_role}</code>.",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text("❌ Не удалось обновить роль пользователя.")

    except Exception as e:
        logger.error("Ошибка при применении новой роли: %s", e, exc_info=True)
        await query.edit_message_text("⚠ Системная ошибка при изменении роли.")
