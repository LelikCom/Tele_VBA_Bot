"""
handler.py

Главный роутер шагов сценария фильтрации строк.
Вызывает соответствующий обработчик в зависимости от текущего шага.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step
from macro.filter_rows import state
from macro.filter_rows.steps import (
    column, mode, range, sheet, confirm
)
from macro.utils import send_response


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text if msg.text else "attachment")
async def process_filter_rows_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главный обработчик сценария фильтрации строк.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с пользовательским состоянием.

    Returns:
        Message: Ответное сообщение (если отправляется).
    """
    if context.user_data.get("state", "").startswith("feedback"):
        print("⏭ Пропуск шага макроса — сейчас feedback")
        return

    handlers = {
        "ask_column": column.ask_column,
        "process_column": column.process_column_input,
        "ask_mode": mode.ask_mode,
        "wait_for_mode": mode.handle_mode_selection,
        "ask_manual_values": mode.ask_manual_values,
        "process_manual_values": mode.process_manual_values,
        "ask_sheet_range": range.ask_sheet_range,
        "process_range_input": range.process_range_input,
        "ask_sheet_name": sheet.ask_sheet_name,
        "process_sheet_name": sheet.process_sheet_name,
        "confirm_macro": confirm.confirm_macro,
        "show_instruction": confirm.show_instruction_options,
    }

    step = state.get_step(context.user_data)
    print(f"🧩 Текущий шаг сценария: {step}")

    try:
        if step in handlers:
            return await handlers[step](update, context)
        else:
            return await handle_unknown_step(update, context)
    except Exception as e:
        logging.exception(f"❌ Ошибка в сценарии: {e}")
        return await handle_scenario_error(update, context)


async def handle_unknown_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка неизвестного шага сценария.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.

    Returns:
        None
    """
    await send_response(update, "⚠️ Неизвестная команда. Начните с /start")
    context.user_data.clear()


async def handle_scenario_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка критической ошибки сценария.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.

    Returns:
        None
    """
    await send_response(update, "❌ Произошла внутренняя ошибка. Попробуйте позже.")
    context.user_data.clear()
