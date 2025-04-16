"""
reply.py

Обработка ответов бота:
- Отправка ответных сообщений пользователям с возможностью прикрепления клавиатуры.
- Логирование вопросов пользователей и ответов бота для отслеживания сценариев.
"""

from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram import InlineKeyboardMarkup

from log_dialog.handlers_diag import log_user_question, log_bot_answer
from log_dialog.models_daig import Point


async def reply_with_log(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    point: Point = Point.UNKNOWN
) -> Message:
    """
    Отправляет ответ пользователю и логирует вопрос/ответ.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
        text (str): Текст ответа.
        reply_markup (InlineKeyboardMarkup | None): Клавиатура (опционально).
        point (Point): Точка сценария (для логирования).

    Returns:
        Message: Отправленное сообщение.
    """
    await log_user_question(update, context, point=point)

    target = (
        update.callback_query.message
        if update.callback_query
        else update.message
    )

    msg = await target.reply_text(text=text, reply_markup=reply_markup)
    await log_bot_answer(update, context, msg, text)
    return msg
