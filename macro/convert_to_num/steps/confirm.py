"""
confirm.py

Финальный шаг сценария "Преобразовать столбец в число": предложение инструкции по вставке макроса.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram import Message
from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def show_instruction_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Отправляет пользователю предложение по поводу инструкции по добавлению макроса в Excel.

    Создаёт клавиатуру с двумя кнопками: одна для подтверждения, другая для отказа от инструкции.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        Message: Ответное сообщение с клавиатурой.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, нужна", callback_data="instruction_yes"),
         InlineKeyboardButton("Нет", callback_data="instruction_no")]
    ])

    if update.callback_query:
        return await update.callback_query.message.reply_text(
            "Нужна ли инструкция по добавлению макроса в Excel?",
            reply_markup=keyboard
        )
    else:
        return await update.message.reply_text(
            "Нужна ли инструкция по добавлению макроса в Excel?",
            reply_markup=keyboard
        )
