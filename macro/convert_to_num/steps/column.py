import logging
from telegram import Update, Message
from telegram.ext import ContextTypes
import re

from log_dialog.logger import CustomLogger
from macro.utils import parse_column, send_response
from log_dialog.handlers_diag import log_bot_answer

logger = CustomLogger(log_to_console=True, log_to_file=True, log_file="column_log.log", log_level=logging.DEBUG, prefix="Column")


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

    message: Message = await send_response(update, msg_text)

    await log_bot_answer(
        update=update,
        context=context,
        msg_obj=message,
        answer_text=msg_text
    )

    logger.info(f"Отправлено сообщение пользователю: {msg_text}")
    context.user_data["macro_step"] = "ask_column_waiting"
    logger.info(f"Переходим к шагу: ask_column_waiting для пользователя {update.effective_user.id}")


async def ask_column_waiting_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ввод столбца от пользователя, поддерживает числовой и буквенный формат.
    Сохраняет выбор в context.user_data, логирует шаги и переходит к следующему этапу.
    """
    if not update.message:
        logger.error("Ожидается текстовое сообщение, но пришло что-то другое.")
        return

    user_input = update.message.text.strip().upper()
    logger.info(f"Получен ввод от пользователя: {user_input}")

    logger.debug(f"Пользователь {update.effective_user.id} ввел столбец: {user_input}")

    column_num = None
    if user_input.isdigit():
        column_num = int(user_input)
        logger.debug(f"Пользователь ввёл числовой столбец: {column_num}")
    elif user_input.isalpha() and len(user_input) == 1 and re.match("^[A-Za-z]$", user_input):
        column_num = ord(user_input) - ord('A') + 1
        logger.debug(f"Пользователь ввёл буквенный столбец: {column_num}")
    else:
        error_text = "❌ Неверный формат столбца.\nПроверь раскладку клавиатуры.\nНужны только английские буквы.\nПример: 1 или A."
        error_msg = await update.message.reply_text(error_text)
        logger.error(f"Ошибка парсинга столбца. Ввод пользователя: {user_input}")

        await log_bot_answer(update, context, msg_obj=error_msg, answer_text=error_text)

        repeat_text = (
            "📍Какой столбец преобразовать?\n"
            "Укажи номер столбца или букву, например: «1» или «A».\n"
            "Если буква — только английская."
        )
        repeat_msg = await update.message.reply_text(repeat_text)
        await log_bot_answer(update, context, msg_obj=repeat_msg, answer_text=repeat_text)
        return

    if not (1 <= column_num <= 16384):
        error_text = "❌ Неверный номер столбца. Должен быть от 1 до 16384."
        error_msg = await update.message.reply_text(error_text)
        logger.error(f"Ошибка парсинга столбца. Ввод пользователя: {user_input}")

        await log_bot_answer(update, context, msg_obj=error_msg, answer_text=error_text)
        return await ask_column_step(update, context)

    context.user_data["column_num"] = column_num
    context.user_data["column_input_type"] = "letter" if user_input.isalpha() else "number"
    logger.info(f"Сохранён номер столбца: {column_num}")

    confirm_text = f"✅ Выбран столбец: {column_num}"
    confirm_msg = await update.message.reply_text(confirm_text)

    logger.debug(f"Перед вызовом log_bot_answer: confirm_msg={confirm_msg}, confirm_text={confirm_text}")
    await log_bot_answer(update, context, msg_obj=confirm_msg, answer_text=confirm_text)

    context.user_data["macro_step"] = "ask_start_cell"
    logger.info(f"Переходим к шагу: {context.user_data} для пользователя {update.effective_user.id}")

    next_prompt = "📍 С какой строки преобразовать?\n Укажи цифру. \n Цифры выглядят так: 1, 2, 5"
    msg = await update.message.reply_text(next_prompt)
    await log_bot_answer(update, context, msg_obj=msg, answer_text=next_prompt)

    logger.info(f"Отправлено сообщение с запросом на следующую строку для пользователя {update.effective_user.id}")

    return confirm_msg
