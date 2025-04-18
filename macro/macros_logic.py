"""
macros_logic.py

Обработка запуска макросов и сценариев, а также возврат кода макроса из базы данных.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.macros import fetch_macro_by_name
from log_dialog.handlers_diag import log_step
from log_dialog.models_daig import Point

from macro.convert_to_num.handler import process_convert_column_scenario
from macro.filter_rows.handler import process_filter_rows_scenario


logger = logging.getLogger(__name__)


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы MarkdownV2 для безопасного отображения текста.

    Args:
        text (str): Текст для экранирования.

    Returns:
        str: Экранированный текст.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return ''.join(f"\\{char}" if char in escape_chars else char for char in text)


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def show_instruction_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Отправляет пользователю предложение по поводу инструкции по добавлению макроса в Excel.

    Функция отображает два варианта ответа: "Да, нужна" и "Нет" через inline клавиатуру.
    В зависимости от выбора пользователя будет выполнено соответствующее действие.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        Message: Ответное сообщение от бота с клавиатурой.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, нужна", callback_data="instruction_yes"),
         InlineKeyboardButton("Нет", callback_data="instruction_no")]
    ])

    if update.callback_query:
        return await update.callback_query.message.reply_text(
            "Нужна ли инструкция по добавлению макроса в Excel?",
            reply_markup=keyboard
        )
    else:
        return await update.message.reply_text(
            "Нужна ли инструкция по добавлению макроса в Excel?",
            reply_markup=keyboard
        )


async def send_error_message(update: Update, message: str) -> None:
    """
    Отправляет сообщение об ошибке пользователю.

    Args:
        update (Update): Объект Telegram.
        message (str): Текст ошибки.
    """
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(message)


async def send_markdown_response(update: Update, message: str) -> None:
    """
    Отправляет пользователю MarkdownV2-сообщение.

    Args:
        update (Update): Объект Telegram.
        message (str): Текст сообщения.
    """
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)


scenario_handlers = {
    "Преобразовать_столбец_в_число": process_convert_column_scenario,
    "Фильтр_Строки": process_filter_rows_scenario
}


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text)
async def run_macro_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message | None:
    """
    Запускает макрос как сценарий, либо возвращает VBA-код из БД.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.

    Returns:
        Optional[Message]: Сообщение Telegram, если было отправлено.
    """
    macro_name = context.user_data.get("current_macro_name")
    if not macro_name:
        logger.error("Не найден macro_name в user_data")
        await send_error_message(update, "Ошибка: не найден macro_name.")
        return

    handler = scenario_handlers.get(macro_name)
    if handler:
        await handler(update, context)

        step = context.user_data.get("macro_step")
        logger.info(f"Сценарий макроса '{macro_name}', шаг: {step}")

        if step is None:
            return await show_instruction_options(update, context)
        return

    logger.info(f"Макрос '{macro_name}' не является сценарием — возвращаем код.")
    return await handle_macro_code(update, context, macro_name)


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text)
async def handle_macro_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    macro_name: str
) -> Message | None:
    """
    Отправляет код макроса по его названию.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.
        macro_name (str): Название макроса.

    Returns:
        Optional[Message]: Ответное сообщение.
    """
    macro_code = await fetch_macro_by_name(macro_name)
    if not macro_code:
        await send_error_message(update, f"Макрос {macro_name} не найден.")
        return

    escaped = escape_markdown_v2(macro_code)
    await send_markdown_response(update, f"Вот код макроса:\n\n```vba\n{escaped}\n```")
    return await show_instruction_options(update, context)
