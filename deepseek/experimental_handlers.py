# deepseek/experimental_handlers.py
from telegram import Update, constants
from telegram.ext import ContextTypes

from deepseek.experimental import WARNING_TEXT, back_keyboard


async def experimental_ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает предупреждение + кнопку «Назад»."""
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        WARNING_TEXT, reply_markup=back_keyboard(), parse_mode=constants.ParseMode.HTML
    )


async def back_to_prev_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет сообщение с предупреждением."""
    q = update.callback_query
    await q.answer()
    await q.message.delete()
