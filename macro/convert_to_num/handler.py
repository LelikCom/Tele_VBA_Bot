"""
handler.py

Главный обработчик шагов сценария "Преобразовать столбец в число".
Роутит логику по текущему шагу в context.user_data.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from macro.convert_to_num.steps import (
    column,
    start_row,
    confirm
)


async def process_convert_column_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Управляет шагами сценария для макроса "Преобразовать столбец в число".

    Эта функция выполняет проверку текущего шага, затем вызывает соответствующую функцию для обработки этого шага.
    Шаги включают: запрос столбца, запрос строки начала, а также показ инструкции. Функция также обрабатывает ошибку,
    если текущий шаг не определен в сценарии.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя, включая информацию о текущем шаге.

    Returns:
        None: Функция выполняет шаги сценария и отправляет ответы пользователю.
    """
    logging.info("[PROCESS_CONVERT] Начало сценария 'Преобразовать столбец в число'")

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
    else:
        logging.error(f"[PROCESS_CONVERT] Неизвестный шаг сценария: {step}")
        await update.message.reply_text("⚠️ Неизвестный шаг сценария.")

