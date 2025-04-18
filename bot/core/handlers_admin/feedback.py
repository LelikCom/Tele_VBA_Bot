"""
feedback.py

Обработка обратной связи в админке:
- Просмотр непрочитанных отзывов
- Открытие конкретного отзыва
- Ответ пользователю
- Переход по страницам отзывов
"""

import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.feedback import (
    fetch_unread_feedback,
    fetch_feedback_by_id,
    mark_feedback_as_read,
)


async def show_feedback_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает список непрочитанных отзывов (5 штук на страницу).

    Args:
        update (Update): Callback от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст пользователя.
    """
    query = update.callback_query
    await query.answer()

    offset = context.user_data.get("feedback_offset", 0)
    rows = await fetch_unread_feedback(limit=5, offset=offset)

    if not rows:
        await query.message.edit_text("✅ Больше непрочитанных отзывов нет.")
        return

    keyboard = []
    for row in rows:
        fid, _, theme, _, _, att_type, _ = row
        label = f"{theme or 'Без темы'} — {att_type or 'текст'}"
        keyboard.append([InlineKeyboardButton(f"📬 {label}", callback_data=f"show_feedback_{fid}")])

    keyboard.append([InlineKeyboardButton("➡️ Следующая страница", callback_data="feedback_next")])

    await query.message.edit_text(
        "Выберите отзыв:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_feedback_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Переход к следующей странице непрочитанных отзывов.

    Args:
        update (Update): Callback от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст пользователя.
    """
    query = update.callback_query
    await query.answer()

    current_offset = context.user_data.get("feedback_offset", 0)
    context.user_data["feedback_offset"] = current_offset + 5
    await show_feedback_list(update, context)


async def show_feedback_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отображает конкретный отзыв (текст + вложение) по его ID.

    Args:
        update (Update): Callback от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст пользователя.
    """
    query = update.callback_query
    await query.answer()

    try:
        fid = int(query.data.replace("show_feedback_", ""))
    except ValueError:
        await query.message.reply_text("❌ Некорректный ID отзыва.")
        return

    row = await fetch_feedback_by_id(fid)
    if not row:
        await query.message.reply_text("❌ Отзыв не найден или уже прочитан.")
        return

    fid, user_id, theme, message, attachment, att_type, created_at = row

    text_parts = [
        f"<b>📨 Отзыв от {user_id}</b>",
        f"<i>{created_at.strftime('%Y-%m-%d %H:%M')}</i>",
    ]
    if theme:
        text_parts.append(f"<b>Тема:</b> {theme}")
    if message:
        text_parts.append(f"\n{message}")
    full_text = "\n".join(text_parts)

    try:
        if attachment and att_type == "photo":
            await query.message.reply_photo(photo=attachment, caption=full_text, parse_mode=ParseMode.HTML)
        elif attachment and att_type == "document":
            await query.message.reply_document(document=attachment, caption=full_text, parse_mode=ParseMode.HTML)
        else:
            await query.message.reply_text(full_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.warning(f"Ошибка при отображении отзыва: {e}")
        await query.message.reply_text(f"⚠️ Ошибка при отправке: {e}")

    mark_feedback_as_read(fid)

    # Кнопка "Ответить"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ Ответить пользователю", callback_data=f"reply_feedback_{fid}_{user_id}")]
    ])
    await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def handle_feedback_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Начинает процесс ответа на отзыв. Сохраняет ID и ожидает текст от админа.

    Args:
        update (Update): Callback от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст пользователя.
    """
    query = update.callback_query
    await query.answer()

    try:
        parts = query.data.split("_")
        fid = int(parts[2])
        user_id = int(parts[3])

        context.user_data["reply_feedback"] = {
            "fid": fid,
            "user_id": user_id
        }

        await query.message.reply_text("✍️ Введите сообщение, которое будет отправлено пользователю:")
    except Exception as e:
        logging.error(f"Ошибка в reply_feedback: {e}")
        await query.message.reply_text("❌ Не удалось начать ответ на отзыв.")
