from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes

from deepseek.experimental import WARNING_TEXT, back_keyboard
from deepseek.formatter import send_long_message, safe_format_html
from deepseek.deepseek_client import DeepSeekClient

api_client = DeepSeekClient()
STATE_KEY = "awaiting_experimental_prompt"


async def start_experimental_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запускает процесс запроса макроса или формулы через экспериментальную функцию.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Side Effects:
        Отправляет сообщение с предупреждением и клавиатурой.
        Устанавливает флаг ожидания пользовательского ввода в context.user_data.
    """
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        WARNING_TEXT + "\n\n✍️ Теперь опиши, какой макрос или формулу создать:",
        reply_markup=back_keyboard(),
        parse_mode=constants.ParseMode.HTML,
    )
    context.user_data[STATE_KEY] = True


async def cancel_experimental(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отменяет процесс создания макроса или формулы через экспериментальную функцию.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Side Effects:
        Удаляет сообщение с предупреждением и сбрасывает флаг ожидания.
    """
    query = update.callback_query
    await query.answer()

    await query.message.delete()
    context.user_data.pop(STATE_KEY, None)


async def experimental_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовый ввод пользователя и отправляет запрос в DeepSeek API.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Side Effects:
        Отправляет промежуточные и итоговые сообщения пользователю.
        Обрабатывает возможные ошибки при запросе к DeepSeek API.
        Сбрасывает режим ожидания после успешной генерации ответа.
    """
    if not context.user_data.get(STATE_KEY):
        return

    prompt = update.message.text.strip()

    status_msg = await update.message.reply_text("⏳ Генерирую макрос, подожди…")

    system_prompt = (
        "Ты выступаешь как 'authdeepseek' — эксперт по VBA и формулам Excel. "
        "Отвечай только кодом (без пояснений) в тройных бэктиках. "
        "Если запрошена формула — дай готовую формулу, если макрос — полноценный VBA-код. "
        "И отправь короткую инструкцию, как добавить это в Excel."
    )

    try:
        response = await api_client.send_message(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            mode="chat",
            web_search=False,
        )

        await status_msg.delete()

        formatted_response = safe_format_html(response)
        await send_long_message(
            update.message, formatted_response, parse_mode=constants.ParseMode.HTML
        )

        context.user_data.pop(STATE_KEY, None)

    except Exception as e:
        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry_experimental")],
                [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")],
            ]
        )
        try:
            await status_msg.edit_text(
                f"🚨 Упс, не вышло:\n<code>{str(e) or 'Неизвестная ошибка'}</code>",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=kb,
            )
        except Exception:
            await update.message.reply_text(
                f"🚨 Ошибка при редактировании сообщения:\n<code>{str(e) or 'Неизвестная ошибка'}</code>",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=kb,
            )


async def retry_experimental(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает повторную попытку ввода запроса для генерации макроса или формулы.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Side Effects:
        Запрашивает у пользователя новое описание макроса или формулы.
        Снова устанавливает флаг ожидания пользовательского ввода в context.user_data.
    """
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        "✍️ Введи новое описание макроса или формулы:",
        parse_mode=constants.ParseMode.HTML,
    )
    context.user_data[STATE_KEY] = True
