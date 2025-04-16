"""
values.py

Обработка шагов макроса для фильтрации строк:
- Запрос значений для фильтрации.
- Обработка введённых значений и их сохранение.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def ask_values_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Запрашивает у пользователя значения для фильтрации.

    Функция отправляет запрос пользователю с просьбой ввести значения для фильтрации,
    разделённые запятой.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция отправляет сообщение с запросом значений и устанавливает следующий шаг.
    """
    await update.message.reply_text("🔢 Введите значения для фильтрации (через запятую):")
    context.user_data["macro_step"] = "values_waiting"


async def ask_values_waiting_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Принимает введённые значения и сохраняет их.

    Функция обрабатывает введённые пользователем значения для фильтрации, очищает их от пробелов
    и сохраняет в контексте пользователя. После этого происходит переход к следующему шагу.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция сохраняет значения и отправляет подтверждение пользователю.
    """
    values = [v.strip() for v in update.message.text.split(",")]
    context.user_data["values"] = values
    context.user_data["macro_step"] = "show_instruction"

    await update.message.reply_text(f"✅ Значения сохранены: {', '.join(values)}")

