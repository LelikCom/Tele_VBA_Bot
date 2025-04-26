from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes

from deepseek.experimental import WARNING_TEXT, back_keyboard
from deepseek.formatter import send_long_message, safe_format_html
from deepseek.deepseek_client import DeepSeekClient

api_client = DeepSeekClient()
STATE_KEY = "awaiting_experimental_prompt"

# ───────────────────────────────────────────────────────────────────
async def start_experimental_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт запроса макроса или формулы."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        WARNING_TEXT + "\n\n✍️ Теперь опиши, какой макрос или формулу создать:",
        reply_markup=back_keyboard(),
        parse_mode=constants.ParseMode.HTML,
    )
    context.user_data[STATE_KEY] = True


async def cancel_experimental(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена запроса макроса или формулы."""
    query = update.callback_query
    await query.answer()

    await query.message.delete()
    context.user_data.pop(STATE_KEY, None)


# ───────────────────────────────────────────────────────────────────
async def experimental_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовый ввод пользователя и отправляет его в DeepSeek."""
    if not context.user_data.get(STATE_KEY):
        return  # если пользователь не в режиме ожидания, игнорируем

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

        # Форматируем ответ и отправляем длинные сообщения частями
        formatted_response = safe_format_html(response)
        await send_long_message(update.message, formatted_response, parse_mode=constants.ParseMode.HTML)

        context.user_data.pop(STATE_KEY, None)  # Сбрасываем режим

    except Exception as e:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry_experimental")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")]
        ])
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
        # Не убираем STATE_KEY — чтобы пользователь мог попробовать снова


async def retry_experimental(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки «Попробовать снова»."""
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        "✍️ Введи новое описание макроса или формулы:",
        parse_mode=constants.ParseMode.HTML,
    )
    context.user_data[STATE_KEY] = True
