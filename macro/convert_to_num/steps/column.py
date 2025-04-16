"""
column.py

Шаги сценария "Преобразовать столбец в число": запрос столбца и его обработка.
"""

import logging
from telegram import Update, Message
from telegram.ext import ContextTypes

from macro.utils import parse_column, send_response
from log_dialog.handlers_diag import log_bot_answer
from macro.convert_to_num.steps.start_row import ask_start_cell_step


async def ask_column_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Запрашивает у пользователя указание столбца.

    Args:
        update (Update): Объект Telegram обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст.

    Returns:
        None
    """
    msg_text = (
        "📍Какой столбец преобразовать?\n"
        "Укажи номер столбца или букву, например: «1» или «A».\n"
        "Если буква — только английская."
    )
    msg: Message = await send_response(update, msg_text)
    await log_bot_answer(update, context, msg, msg_text)

    context.user_data["macro_step"] = "ask_column_waiting"


async def ask_column_waiting_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ввод столбца от пользователя. Поддерживает числовой и буквенный формат.
    Сохраняет выбор в context.user_data, логирует шаги, переходит к следующему этапу.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция отправляет сообщения в чат в зависимости от состояния.
    """
    if not update.message:
        logging.error("Ожидается текстовое сообщение, но пришло что-то другое.")
        return

    user_input = update.message.text.strip().upper()
    logging.info(f"Получен ввод от пользователя: {user_input}")

    if any('А' <= c <= 'Я' or 'а' <= c <= 'я' for c in user_input):
        error_text = "❌ Не верный формат столбца.\n Проверь раскладку клавиатуры.\n Нужны только английские буквы.\n Пример: 1 или A."
        error_msg = await update.message.reply_text(error_text)
        await log_bot_answer(update, context, msg_obj=error_msg, answer_text=error_text)
        logging.error(f"Ошибка парсинга столбца. Ввод пользователя: {user_input}")

        repeat_text = (
            "📍Какой столбец преобразовать?\n"
            "Укажи номер столбца или букву, например: «1» или «A».\n"
            "Если буква — только английская."
        )
        repeat_msg = await update.message.reply_text(repeat_text)
        await log_bot_answer(update, context, msg_obj=repeat_msg, answer_text=repeat_text)
        return

    column_num = None
    if user_input.isdigit():
        column_num = int(user_input)
    elif user_input.isalpha() and len(user_input) == 1:
        column_num = ord(user_input) - ord('A') + 1
    elif len(user_input) > 1 and user_input.isalpha():
        column_num = 0

    if column_num is None or not (1 <= column_num <= 16384):
        error_text = "❌ Неверный формат столбца.\nПроверьте раскладку клавиатуры.\nПример: 1 или A."
        error_msg = await update.message.reply_text(error_text)
        await log_bot_answer(update, context, msg_obj=error_msg, answer_text=error_text)
        logging.error(f"Ошибка парсинга столбца. Ввод пользователя: {user_input}")

        repeat_text = (
            "📍Какой столбец преобразовать?\n"
            "Укажи номер столбца или букву, например: «1» или «A».\n"
            "Если буква — только английская."
        )
        repeat_msg = await update.message.reply_text(repeat_text)
        await log_bot_answer(update, context, msg_obj=repeat_msg, answer_text=repeat_text)
        return

    context.user_data["column_num"] = column_num
    logging.info(f"Сохранён номер столбца: {column_num}")

    confirm_text = f"✅ Выбран столбец: {column_num}"
    confirm_msg = await update.message.reply_text(confirm_text)
    await log_bot_answer(update, context, msg_obj=confirm_msg, answer_text=confirm_text)

    context.user_data["macro_step"] = "ask_start_cell"
    logging.info("Переходим к шагу: ask_start_cell")

    next_prompt = "📍 С какой строки преобразовать? (Пример: 1, 2, 5 и т.д.)"
    msg = await update.message.reply_text(next_prompt)
    await log_bot_answer(update, context, msg_obj=msg, answer_text=next_prompt)


