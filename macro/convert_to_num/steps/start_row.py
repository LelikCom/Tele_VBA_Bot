"""
start_row.py

Шаг сценария "Преобразовать столбец в число": ввод стартовой строки и генерация макроса.
"""

import logging
from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step
from db.macros import fetch_macro_by_name
from macro.utils import send_response, escape_markdown_v2
from db.dialog_log import insert_question
from log_dialog.handlers_diag import log_bot_answer

from macro.convert_to_num.steps import (
    column,
    confirm,
    start_row,
)


def column_letter_to_number(col_letter: str) -> int:
    """
    Преобразует букву столбца в его номер.
    Например, 'A' -> 1, 'B' -> 2, и так далее.

    Args:
        col_letter (str): Буква столбца (например, 'A', 'B').

    Returns:
        int: Номер столбца (например, для 'A' возвращает 1, для 'B' возвращает 2).
    """
    col_letter = col_letter.upper()
    return ord(col_letter) - ord('A') + 1


async def process_convert_column_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Управляет шагами сценария для макроса "Преобразовать столбец в число".

    Эта функция проверяет текущий шаг сценария и выполняет соответствующие действия:
    - Шаги для ввода столбца, ввода строки старта и подтверждения инструкции.
    - Переход между шагами, обновление состояния (macro_step) после выполнения каждого шага.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        None: Функция не возвращает значения, но отправляет сообщения и обновляет состояние.
    """
    logging.info(f"[PROCESS_CONVERT] Начало сценария 'Преобразовать столбец в число'.")

    steps = {
        "ask_column": column.ask_column_step,
        "ask_column_waiting": column.ask_column_waiting_step,
        "ask_start_cell": start_row.ask_start_cell_step,
        "show_instruction": confirm.show_instruction_options,
    }

    step = context.user_data.get("macro_step", "ask_column")
    logging.info(f"[PROCESS_CONVERT] Текущий шаг: {step}")

    if step in steps:
        logging.info(f"[PROCESS_CONVERT] Переход к шагу: {step}")
        await steps[step](update, context)

        if step == "ask_column":
            context.user_data["macro_step"] = "ask_start_cell"
        elif step == "ask_start_cell":
            context.user_data["macro_step"] = "show_instruction"
        elif step == "show_instruction":
            logging.info("[PROCESS_CONVERT] Сценарий завершён.")
            context.user_data["macro_step"] = "completed"
    else:
        logging.error(f"[PROCESS_CONVERT] Неизвестный шаг сценария: {step}")
        await update.message.reply_text("⚠️ Неизвестный шаг сценария. Попробуйте начать сначала.")

        context.user_data["macro_step"] = "ask_column"
        return


@log_step(question_point=Point.START_ROW)
async def ask_start_cell_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ввод начальной строки и генерирует итоговый макрос.

    Функция проверяет ввод пользователя на корректность, сохраняет начальную строку,
    генерирует макрос для преобразования столбца в число, и переходит к следующему этапу.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция отправляет сообщения в чат в зависимости от состояния и выполняет переход к следующему шагу.
    """
    if not update.message:
        await update.callback_query.answer("Ожидается текстовый ввод!")
        logging.error("[START_CELL] Запуск без текстового сообщения.")
        return

    user_input = update.message.text.strip()
    logging.info(f"[START_CELL] Введено пользователем: {user_input}")

    await insert_question(
        user_id=update.effective_user.id,
        username=update.effective_user.username,
        message_id=update.message.message_id,
        message_text=user_input,
        point=Point.START_ROW,
    )

    if not user_input.isdigit():
        error_text = "❌ Неверный формат номера строки.\nНужны цифры. \nПример: 1, 2 и т.д."
        bot_msg = await send_response(update, error_text)
        await log_bot_answer(update, context, bot_msg, error_text)
        logging.warning(f"[START_CELL] Некорректный ввод строки: {user_input}")

        repeat_text = "📍 С какой строки преобразовать?\n Укажи цифру. \n Цифры выглядят так: 1, 2, 5"
        repeat_msg = await send_response(update, repeat_text)
        await log_bot_answer(update, context, repeat_msg, repeat_text)
        return

    start_cell = int(user_input)
    context.user_data["start_cell"] = start_cell
    logging.info(f"[START_CELL] Сохранена стартовая строка: {start_cell}")

    confirm_text = f"✅ Начнём со строки: {start_cell}"
    confirm_msg = await send_response(update, confirm_text)
    await log_bot_answer(update, context, confirm_msg, confirm_text)

    macro_template = await fetch_macro_by_name("Преобразовать_столбец_в_число")
    if not macro_template:
        error_text = "⚠️ Макрос 'Преобразовать столбец в число' не найден в базе данных."
        err_msg = await send_response(update, error_text)
        await log_bot_answer(update, context, err_msg, error_text)
        context.user_data.pop("macro_step", None)
        logging.error("[START_CELL] Шаблон макроса не найден.")
        return

    column_num = context.user_data.get("column_num")
    if not column_num:
        error_text = "⚠️ Номер столбца не найден! Возможно, вы пропустили предыдущий шаг."
        err_msg = await send_response(update, error_text)
        await log_bot_answer(update, context, err_msg, error_text)
        logging.error(f"[START_CELL] column_num отсутствует: {context.user_data}")
        return

    final_macro = (
        macro_template
        .replace("{user_input_column}", str(column_num))
        .replace("{user_input_start_cell}", str(start_cell))
    )
    final_macro = escape_markdown_v2(final_macro)
    logging.info(f"[START_CELL] Сгенерирован макрос для столбца {str(column_num)}, строки {start_cell}")

    macro_msg_text = f"Твой макрос:\n\n```vba\n{final_macro}\n```"
    macro_msg = await send_response(update, macro_msg_text, parse_mode=ParseMode.MARKDOWN_V2)
    await log_bot_answer(update, context, macro_msg, macro_msg_text)

    context.user_data["macro_step"] = "show_instruction"
    logging.info("[START_CELL] Переход к следующему шагу: show_instruction")
    await process_convert_column_scenario(update, context)




