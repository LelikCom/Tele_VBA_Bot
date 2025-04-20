"""
handle_contact.py

Обрабатывает получение номера телефона от пользователя и отправку заявки на авторизацию.
"""

import os
import re
import logging
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.users import update_user_role

from log_dialog.handlers_diag import log_bot_answer

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

logger = logging.getLogger(__name__)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает контакт пользователя (номер телефона), сохраняет его и отправляет заявку админу.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст, содержащий информацию о пользователе.
    """
    user = update.effective_user
    contact = update.message.contact

    raw_phone = contact.phone_number
    clean_phone = re.sub(r"[^\d]", "", raw_phone)
    if not clean_phone.startswith("7"):
        clean_phone = "7" + clean_phone.lstrip("7")

    context.user_data["phone_number"] = clean_phone

    await update_user_role(user.id, "preauth", clean_phone)

    await update.message.reply_text(
        text="✅ Заявка принята! Ожидай подтверждения",
        reply_markup=ReplyKeyboardRemove()
    )

    text = (
        "📄 Заявка пользователя:\n"
        f"• Пользователь: @{user.username or 'без username'}\n"
        f"• ID: {user.id}\n"
        f"• Номер: {clean_phone}"
    )
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"auth_approve_{user.id}_{clean_phone}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"auth_reject_{user.id}_{clean_phone}")
    ], [
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_roles")
    ]])

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN
    )

    logger.info("Заявка отправлена администратору %s", ADMIN_CHAT_ID)


async def handle_authorization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Инициирует процесс авторизации, отправляя пользователю клавиатуру для отправки номера телефона.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о пользователе.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        None: Функция ничего не возвращает, но отправляет сообщение с клавиатурой и логирует действия.
    """
    try:
        logger.info("Инициирование процесса авторизации для пользователя: %s", update.effective_user.id)

        contact_button = KeyboardButton(
            text="📲 Отправить номер телефона",
            request_contact=True
        )
        keyboard = [[contact_button]]

        msg_obj = await update.callback_query.message.reply_text(
            text="📱 Для авторизации отправь свой номер:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        await log_bot_answer(
            update=update,
            context=context,
            msg_obj=msg_obj,
            answer_text="📱 Для авторизации отправь свой номер:"
        )

        logger.debug("Клавиатура с запросом контакта отправлена")

    except Exception as e:
        logger.error("Ошибка при обработке авторизации: %s", e, exc_info=True)
        await update.callback_query.answer("Произошла ошибка. Попробуйте позже.")

