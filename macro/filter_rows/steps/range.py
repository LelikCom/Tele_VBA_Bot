"""
range.py

Шаги сценария фильтрации: запрос и обработка диапазона ячеек.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from macro.filter_rows import state
from macro.utils import send_response, validate_cell, RANGE_PATTERN
from log_dialog.handlers_diag import log_bot_answer
from macro.filter_rows.steps.sheet import ask_sheet_name
from macro.filter_rows.steps.confirm import confirm_macro


async def ask_sheet_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запрашивает у пользователя диапазон ячеек.

    Функция просит пользователя ввести диапазон ячеек с использованием английских букв и
    отправляет сообщение с примерами правильного формата.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция отправляет запрос на ввод диапазона и устанавливает следующий шаг.
    """
    await send_response(
        update,
        "📍Из какого диапазона будем забирать данные?\n"
        "Укажите диапазон значений с английскими буквами.\n"
        "Примеры:\n• A1:B10\n• Лист1!C5:D20"
    )
    state.set_step(context.user_data, "process_range_input")


async def process_range_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода диапазона ячеек, поддерживает формы: A1:B2 или Лист1!A1:B2.

    Функция проверяет введённый диапазон на соответствие формату, проверяет корректность ячеек,
    сохраняет результат в контексте и переходит к следующему шагу.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция обрабатывает ввод диапазона, подтверждает выбор и переходит к следующему шагу.
    """
    raw_input = update.message.text.strip()
    cleaned_input = raw_input.replace("I", "!").replace(" ", "")
    logging.info(f"Получен диапазон: {cleaned_input}")

    if not RANGE_PATTERN.match(cleaned_input):
        error_text = "❌ Неверный формат диапазона.\nПроверьте раскладку клавиатуры.\nПример: A1:B10 или Лист1!C5:D20"
        msg = await send_response(update, error_text)
        await log_bot_answer(update, context, msg, error_text)
        await ask_sheet_range(update, context)
        return

    try:
        if "!" in cleaned_input:
            sheet, range_part = cleaned_input.split("!", 1)
            range_part = range_part.upper()
            sheet = sheet.strip()
            final_range = f"{sheet}!{range_part}"
            context.user_data["sheet"] = sheet
        else:
            range_part = cleaned_input.upper()
            final_range = range_part

        cells = range_part.split(":")
        for cell in cells:
            if not validate_cell(cell):
                raise ValueError(f"Некорректная ячейка: {cell}")

        context.user_data["selected_range"] = final_range
        next_step = "ask_sheet_name" if "!" not in final_range else "confirm_macro"
        context.user_data["macro_step"] = next_step

        confirm_text = f"✅ Выбран диапазон: {final_range}"
        confirm_msg = await send_response(update, confirm_text)
        await log_bot_answer(update, context, confirm_msg, confirm_text)

        await (ask_sheet_name if next_step == "ask_sheet_name" else confirm_macro)(update, context)

    except ValueError as e:
        error_text = f"❌ {str(e)}"
        msg = await send_response(update, error_text)
        await log_bot_answer(update, context, msg, error_text)
        context.user_data["macro_step"] = "process_range_input"


