from telegram import Update
from telegram.ext import ContextTypes
import logging
import json
import os

from db.users import get_user_role

from log_dialog.handlers_diag import log_step
from log_dialog.models_daig import Point

from bot.core.auth_user.handle_contact import handle_authorization
from bot.core.utils.sql_utils import reply_with_log
from bot.core.handlers_admin.sql_tools import handle_sql_entry
from bot.core.handlers_for_all.handle_vba import (
    handle_formulas,
    handle_macros,
    handle_instruction_yes,
    handle_instruction_no,
    handle_back_to_main,
    handle_filter_role,
    handle_show_more_users,
    handle_macro_detail,
    handle_formula_detail,
    handle_joke_of_the_day,
)


# Загрузка разрешённых действий
json_path = os.path.join(os.path.dirname(__file__), "..", "core", "auth_user", "allowed_actions.json")
with open(os.path.abspath(json_path), "r", encoding="utf-8") as f:
    allowed_actions = json.load(f)

logger = logging.getLogger(__name__)


@log_step(question_point=Point.TEXT, answer_text_getter=lambda msg: msg.text)
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает нажатия на inline-кнопки, определяет тип действия и перенаправляет
    в соответствующую функцию-обработчик.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о нажатой кнопке.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        None: Функция ничего не возвращает, но отправляет сообщения в чат и перенаправляет на обработчики.
    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    try:
        user_id = update.effective_user.id
        user_role = await get_user_role(user_id)
        data = query.data

        action = next((key for key in allowed_actions if data == key or data.startswith(f"{key}:")), None)
        if action and user_role not in allowed_actions[action]:
            return await query.message.reply_text("⚠ У вас нет прав для выполнения данного действия.")

        handlers = {
            "authorization": handle_authorization,
            "formulas": handle_formulas,
            "macros": handle_macros,
            "instruction_yes": handle_instruction_yes,
            "instruction_no": handle_instruction_no,
            "sql_requests": handle_sql_entry,
            "joke_of_the_day": handle_joke_of_the_day,
            "back_to_main": handle_back_to_main
        }

        if data.startswith("formula:"):
            return await handle_formula_detail(update, context)
        elif data.startswith("macro:"):
            return await handle_macro_detail(update, context)
        elif data.startswith("filter_role_"):
            return await handle_filter_role(update, context)
        elif data.startswith("show_more_"):
            return await handle_show_more_users(update, context)
        elif data.startswith("user_select_"):
            return  # Обрабатывается в другом месте
        elif data in handlers:
            return await handlers[data](update, context)

    except Exception as e:
        logger.exception("Ошибка обработки callback")
        return await reply_with_log(update, context, "⚠ Произошла ошибка при обработке запроса", point=Point.ERROR)
