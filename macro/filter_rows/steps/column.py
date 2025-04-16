"""
column.py

Шаги сценария фильтрации: ввод и обработка столбца.
"""

from telegram import Update
from telegram.ext import ContextTypes

from macro.utils import send_response, parse_column
from macro.filter_rows import state


async def ask_column(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запрашивает у пользователя столбец для фильтрации.

    Args:
        update (Update): Объект Telegram обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст.

    Returns:
        None
    """
    await send_response(
        update,
        "📍Какой столбец будем фильтровать?\n"
        "Укажите номер столбца или букву, например: «1» или «A».\n"
        "Если буква — только английская."
    )
    state.set_step(context.user_data, "process_column")


async def process_column_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод столбца и сохраняет его в состояние.

    Args:
        update (Update): Объект Telegram обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст.

    Returns:
        None
    """
    user_input = update.message.text.strip().upper()
    column_num = parse_column(user_input)

    if column_num is None or not (1 <= column_num <= 16384):
        await send_response(
            update,
            "❌ Неверный формат столбца.\n"
            "Проверьте раскладку клавиатуры.\n"
            "Нужны только английские буквы.\n"
            "Пример: 1 или A."
        )
        return await ask_column(update, context)

    context.user_data["column_num"] = column_num
    await send_response(update, f"✅ Выбран столбец: {column_num}")
    state.set_step(context.user_data, "ask_mode")

    from macro.filter_rows.steps import mode
    await mode.ask_mode(update, context)
