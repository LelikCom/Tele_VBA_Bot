"""
sheet.py

Шаг сценария фильтрации: запрос имени листа и его валидация.
"""

import re
from telegram import Update
from telegram.ext import ContextTypes

from macro.utils import send_response
from macro.filter_rows import state
from log_dialog.handlers_diag import log_bot_answer
from macro.filter_rows.steps.confirm import confirm_macro


async def ask_sheet_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запрашивает у пользователя имя листа.

    Функция отправляет запрос пользователю с просьбой ввести имя листа.
    Рекомендуется скопировать имя листа из файла, чтобы избежать ошибок.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция отправляет запрос и устанавливает следующий шаг.
    """
    prompt_text = (
        "📍 Введите имя листа.\n"
        "Лучше скопировать из файла, чтобы не ошибаться 🤓"
    )
    msg = await send_response(update, prompt_text)
    await log_bot_answer(update, context, msg, prompt_text)
    state.set_step(context.user_data, "process_sheet_name")


async def process_sheet_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода имени листа с валидацией.

    Функция выполняет проверку на пустоту, длину и наличие запрещённых символов
    в имени листа. Если имя листа некорректно, отправляется соответствующее сообщение об ошибке.
    После успешной валидации имя листа сохраняется в контексте и сценарий переходит к следующему шагу.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        None: Функция выполняет валидацию и переходит к следующему шагу.
    """
    sheet_name = update.message.text.strip()

    if not sheet_name:
        await update.message.reply_text("❌ Имя листа не может быть пустым.")
        return

    if len(sheet_name) > 31:
        await update.message.reply_text("❌ Максимальная длина имени листа — 31 символ.")
        return

    forbidden_chars = r'[\\/?*[\]]'
    if re.search(forbidden_chars, sheet_name):
        await update.message.reply_text(
            "❌ Имя листа содержит запрещенные символы: \\ / ? * [ ]"
        )
        await ask_sheet_name(update, context)
        return

    context.user_data["sheet"] = sheet_name
    context.user_data["macro_step"] = "confirm_macro"
    await confirm_macro(update, context)

    context.user_data["macro_step"] = None
