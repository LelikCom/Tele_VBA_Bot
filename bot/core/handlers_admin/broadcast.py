"""
broadcast.py

Модуль для работы с рассылками администратора:
- Выбор роли
- Ввод даты/времени
- Ввод текста или фото
- Предпросмотр и подтверждение
- Рассылка сообщений
"""

import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import ContextTypes

from db.users import get_users_by_role, get_all_roles_from_db
from bot.core.utils.admin_utils import is_admin, reset_all_user_state


async def admin_broadcast_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Точка входа в рассылку. Предлагает выбрать роль получателей.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с состоянием пользователя.
    """
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.callback_query.answer("⛔ Недостаточно прав.")
        return

    await update.callback_query.answer()
    reset_all_user_state(context)
    context.user_data["state"] = "broadcast:choose_role"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Пользователям", callback_data="broadcast_role_auth")],
        [InlineKeyboardButton("🛠 Админам", callback_data="broadcast_role_admin")],
        [InlineKeyboardButton("👤 Всем", callback_data="broadcast_role_all")],
    ])

    await update.callback_query.message.edit_text(
        "👥 Кому вы хотите отправить рассылку?",
        reply_markup=keyboard
    )


async def handle_broadcast_choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает выбор роли для рассылки и предлагает ввести дату/время.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с состоянием пользователя.
    """
    query = update.callback_query
    await query.answer()
    role_code = query.data.replace("broadcast_role_", "")
    context.user_data["broadcast_target_role"] = role_code
    context.user_data["state"] = "broadcast:datetime"

    await query.message.edit_text(
        "📅 Введите дату и время обновления.\nНапример:\n`12.04.2025 20:00`",
        parse_mode="Markdown"
    )


async def handle_broadcast_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает дату и время от администратора.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с состоянием пользователя.
    """
    text = update.message.text.strip()

    if text.lower() in ["отмена", "/cancel"]:
        context.user_data.clear()
        await update.message.reply_text("🚫 Рассылка отменена.")
        return

    try:
        dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        context.user_data["broadcast_datetime"] = dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        await update.message.reply_text(
            "❗ Формат даты неверен. Укажите в формате: `12.04.2025 20:00`",
            parse_mode="Markdown"
        )
        return

    context.user_data["state"] = "broadcast:whats_new"

    await update.message.reply_text(
        "📌 Теперь введите описание «Что нового».\n"
        "Вы можете отправить просто текст или прикрепить фото с подписью.\n\n"
        "Отправьте сообщение или фото ⬇️"
    )


async def send_broadcast_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет администратору предпросмотр рассылки с кнопками подтверждения.

    Включает дату, блок "Что нового", автора и (если есть) фото.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о чате и сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя и настройки рассылки.

    Returns:
        None: Функция ничего не возвращает, но отправляет предпросмотр рассылки с кнопками подтверждения.
    """
    chat_id = update.effective_chat.id

    dt = context.user_data.get("broadcast_datetime", "не указано")
    whats_new = context.user_data.get("broadcast_whats_new", {})
    author = context.user_data.get("broadcast_author", "—")

    text_block = whats_new.get("text", "")
    photo_id = whats_new.get("photo_file_id")

    preview_text = (
        f"📢 <b>Предпросмотр рассылки:</b>\n\n"
        f"<b>Дата и время обновления:</b> {dt}\n\n"
        f"<b>Что нового:</b>\n{text_block}\n\n"
        f"<b>Опубликовал:</b> {author}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Разослать", callback_data="broadcast_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")]
    ])

    if photo_id:
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo_id,
            caption=preview_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=preview_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    context.user_data["last_bot_message_id"] = msg.message_id


async def handle_broadcast_whats_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает текст или фото с подписью (что нового).

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с состоянием пользователя.
    """
    message = update.message

    if message.text and message.text.lower() in ["отмена", "/cancel"]:
        context.user_data.clear()
        await message.reply_text("🚫 Рассылка отменена.")
        return

    if message.photo:
        photo_id = message.photo[-1].file_id
        caption = message.caption or ""
        context.user_data["broadcast_whats_new"] = {
            "photo_file_id": photo_id,
            "text": caption,
        }
    elif message.text:
        context.user_data["broadcast_whats_new"] = {
            "photo_file_id": None,
            "text": message.text,
        }
    else:
        await message.reply_text("❗ Отправьте текст или фото с подписью.")
        return

    context.user_data["broadcast_author"] = "https://t.me/AIchetovkin"
    context.user_data["state"] = "broadcast:confirm"

    await send_broadcast_preview(update, context)


async def handle_broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает отмену рассылки (по кнопке "❌ Отмена").

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    print("[DEBUG] Кнопка ОТМЕНА — вызов функции handle_broadcast_cancel")
    await update.callback_query.answer()
    context.user_data.clear()

    try:
        if update.callback_query.message.photo:
            await update.callback_query.message.edit_caption("🚫 Рассылка отменена.")
        else:
            await update.callback_query.message.edit_text("🚫 Рассылка отменена.")
    except Exception as e:
        logging.error(f"Ошибка при отмене рассылки: {e}")


async def handle_broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Подтверждает и запускает рассылку сообщения выбранной роли.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    logging.info("[DEBUG] Кнопка РАССЫЛКА — вызов функции handle_broadcast_confirm")
    query = update.callback_query
    await query.answer()

    dt = context.user_data.get("broadcast_datetime", "—")
    whats_new = context.user_data.get("broadcast_whats_new", {})
    author = context.user_data.get("broadcast_author", "—")
    text_block = whats_new.get("text", "")
    photo_id = whats_new.get("photo_file_id")
    target_role = context.user_data.get("broadcast_target_role", "auth")

    final_text = (
        f"<b>📢 Обновление</b>\n\n"
        f"<b>Дата и время:</b> {dt}\n\n"
        f"<b>Что нового:</b>\n{text_block}\n\n"
        f"<b>Опубликовал:</b> {author}"
    )

    if target_role == "all":
        roles = await get_all_roles_from_db()
        user_ids = []
        for role in roles:
            users_for_role = await get_users_by_role(role)
            user_ids.extend(users_for_role)
        user_ids = list(set(user_ids))
    else:
        user_ids = await get_users_by_role(target_role)

    success, failed = 0, 0
    for user_id in user_ids:
        try:
            if photo_id:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo_id,
                    caption=final_text,
                    parse_mode="HTML"
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=final_text,
                    parse_mode="HTML"
                )
            success += 1
        except Exception as e:
            logging.error(f"Не удалось отправить пользователю {user_id}: {e}")
            failed += 1

    confirm_text = (
        f"✅ Рассылка завершена!\n\n"
        f"Успешно: {success} ✅\nНе удалось: {failed} ❌"
    )

    try:
        if query.message.photo:
            await query.message.edit_caption(confirm_text)
        else:
            await query.message.edit_text(confirm_text)
    except Exception as e:
        logging.error(f"Ошибка при финальном сообщении: {e}")

    context.user_data.clear()
