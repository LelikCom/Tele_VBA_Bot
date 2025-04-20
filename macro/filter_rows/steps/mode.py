"""
mode.py

Шаги сценария фильтрации: выбор режима и ручной ввод значений.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import ContextTypes
import logging

from macro.utils import send_response
from macro.filter_rows import state

from log_dialog.models_daig import Point

from log_dialog.handlers_diag import (
    log_step,
    log_bot_answer,
)

from macro.filter_rows.steps.column import (
    ask_column,
    process_column_input,
)
from macro.filter_rows.steps.range import (
    ask_sheet_range,
    process_range_input,
)

from macro.filter_rows.steps.sheet import (
    ask_sheet_name,
    process_sheet_name,
)

from macro.filter_rows.steps.confirm import (
    confirm_macro,
    show_instruction_options,
)


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


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text if msg.text else "attachment")
async def process_filter_rows_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главный обработчик сценария для фильтрации строк.

    Эта функция управляет переходом между шагами сценария фильтрации строк. В зависимости от текущего шага сценария
    она вызывает соответствующие обработчики. Если текущий шаг не определён, или происходит ошибка, она возвращает
    сообщение об ошибке или пропускает выполнение шага.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        Message: Ответное сообщение от бота, в зависимости от выполненного шага.
    """
    if context.user_data.get("state", "").startswith("feedback"):
        print("⏭ Пропуск шага макроса — сейчас feedback")
        return

    handlers = {
        "ask_column": ask_column,
        "process_column": process_column_input,
        "ask_mode": ask_mode,
        "wait_for_mode": handle_mode_selection,
        "ask_manual_values": ask_manual_values,
        "process_manual_values": process_manual_values,
        "ask_sheet_range": ask_sheet_range,
        "process_range_input": process_range_input,
        "ask_sheet_name": ask_sheet_name,
        "process_sheet_name": process_sheet_name,
        "confirm_macro": confirm_macro,
        "show_instruction": show_instruction_options,
    }

    step = context.user_data.get("macro_step", "ask_column")

    try:
        if step in handlers:
            result = await handlers[step](update, context)
            return result
        else:
            return await handle_unknown_step(update, context)
    except Exception as e:
        print(f"❌ Ошибка в сценарии: {e}")
        return await handle_scenario_error(update, context)


@log_step(
    question_point=Point.CONFIRM,
    answer_text_getter=lambda msg: getattr(msg, 'text', '') or "Выбор способа задания значений"
)
async def ask_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Показывает пользователю выбор режима ввода значений.

    Функция отображает два варианта выбора: ввод значений вручную или из диапазона.
    После выбора пользователя переход к следующему шагу, в зависимости от выбранного способа.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        Message: Ответное сообщение с клавиатурой выбора.
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Вручную", callback_data="manual"),
            InlineKeyboardButton("Из диапазона", callback_data="range")
        ]
    ])

    state.set_step(context.user_data, "wait_for_mode")
    msg = await send_response(update, "📍Выбери способ задания значений:", keyboard)
    return msg


async def handle_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка выбора режима.

    Функция обрабатывает выбор пользователя из предложенных вариантов (вручную или из диапазона)
    и в зависимости от выбранного варианта, переходит к соответствующему шагу сценария.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция выполняет переход к следующему шагу в сценарии.
    """
    query = update.callback_query
    await query.answer()

    context.user_data["mode"] = query.data
    next_step = "ask_manual_values" if query.data == "manual" else "ask_sheet_range"

    context.user_data["macro_step"] = next_step
    await process_filter_rows_scenario(update, context)


async def ask_manual_values(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запрашивает у пользователя значения для фильтрации вручную.

    Args:
        update (Update): Объект Telegram обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст.

    Returns:
        None
    """
    message = await send_response(
        update,
        "✍️ Введи значения через запятую:\nПример: Яблоки, 123, Текст"
    )

    state.set_step(context.user_data, "process_manual_values")

    logging.info(f"Текущий шаг после установки: {context.user_data.get('macro_step')}")

    await log_bot_answer(
        update=update,
        context=context,
        msg_obj=message,
        answer_text="✍️ Введи значения через запятую:\nПример: Яблоки, 123, Текст"
    )


async def process_manual_values(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ручного ввода значений.

    Функция обрабатывает ввод значений пользователем в виде строки, разделённой запятыми.
    Значения очищаются от лишних пробелов и сохраняются в контексте пользователя.
    Если данные не были введены, функция запрашивает повторный ввод.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция выполняет сохранение значений и переход к следующему шагу.
    """
    values = [v.strip() for v in update.message.text.split(",") if v.strip()]

    if not values:
        await send_response(update, "❌ Нет данных. Попробуйте снова")
        return await ask_manual_values(update, context)

    context.user_data["values"] = [f'"{v}"' for v in values]
    context.user_data["macro_step"] = "confirm_macro"
    await confirm_macro(update, context)
