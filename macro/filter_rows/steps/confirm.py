"""
confirm.py

Финальный шаг сценария фильтрации: генерация макроса и показ инструкции.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.macros import fetch_macro_by_name
from macro.utils import send_response
from macro.filter_rows.logic import build_macro_from_context
from macro.filter_rows import state
from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step


@log_step(
    question_point=Point.SCENARIO,
    answer_text_getter=lambda msg: msg.text if msg.text else "attachment"
)
async def confirm_macro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Подтверждает макрос, строит его на основе данных, сохранённых в контексте пользователя,
    и отправляет пользователю сгенерированный макрос.

    Функция проверяет, есть ли все необходимые данные в контексте для выбранного режима (manual или range),
    затем получает макрос, генерирует код макроса и отправляет его пользователю.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        Message: Ответное сообщение от бота с сгенерированным макросом или сообщением об ошибке.
    """
    logging.info("Начало выполнения confirm_macro")

    required = {
        "manual": ["column_num", "values"],
        "range": ["column_num", "selected_range", "sheet"]
    }

    mode = context.user_data.get("mode")
    logging.info(f"Текущий режим: {mode}")

    missing = [f for f in required.get(mode, []) if f not in context.user_data]
    logging.info(f"Недостающие данные: {missing}")

    if not mode or missing:
        return await send_response(update, "❌ Ошибка конфигурации сценария.")

    try:
        logging.info("Пытаемся получить макрос по имени 'Фильтр_Строки'")
        macro_template = fetch_macro_by_name("Фильтр_Строки")

        if not macro_template:
            raise ValueError("Макрос не найден в базе данных")

        logging.info("Макрос найден, строим макрос...")
        macro_code = build_macro_from_context(macro_template, context.user_data)

        msg = await send_response(
            update,
            f"✅ Твой макрос:\n```vba\n{macro_code}\n```",
            parse_mode=ParseMode.MARKDOWN_V2
        )

        logging.info("Переход к следующему шагу: show_instruction")
        state.set_step(context.user_data, "show_instruction")
        await show_instruction_options(update, context)

        return msg

    except Exception as e:
        import traceback
        logging.error(f"Ошибка генерации макроса: {str(e)}\n{traceback.format_exc()}")
        return await send_response(
            update,
            f"⚠️ Ошибка генерации макроса:\n<code>{e}</code>",
            parse_mode=ParseMode.HTML
        )


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def show_instruction_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Отправляет пользователю предложение по поводу инструкции по добавлению макроса в Excel.

    Эта функция отображает два варианта ответа: "Да, нужна" и "Нет" через inline клавиатуру.
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

