"""
stats.py

Обработчики административной статистики:
- Просмотр скорости ответа за период (час / день / всё время)
"""

import asyncio
import logging
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes

from db.logs import get_average_response_time
from bot.core.utils.admin_utils import get_now_msk
from bot.core.keyboards.admin_panel import (
    get_speed_stats_period_keyboard,
    get_admin_panel_keyboard,
)


async def handle_admin_speed_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отображает клавиатуру выбора периода для анализа статистики.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="⚡ Выберите период для анализа скорости ответа:",
        reply_markup=get_speed_stats_period_keyboard()
    )


async def handle_admin_speed_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает среднюю скорость ответа за выбранный период.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    query = update.callback_query
    await query.answer()

    period_code = query.data.split("_")[-1]
    now = get_now_msk()

    if period_code == "hour":
        since = now - timedelta(hours=1)
        label = "за последний час"
    elif period_code == "day":
        since = now - timedelta(days=1)
        label = "за последний день"
    else:
        since = None
        label = "за всё время"

    avg_seconds = get_average_response_time(since)

    if avg_seconds is None:
        text = f"⚠ Нет данных {label}."
    else:
        text = f"⚡ Средняя скорость ответа {label}: {avg_seconds:.2f} сек"

    old_msg_id = context.user_data.get("last_bot_message_id")
    if old_msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=old_msg_id)
        except Exception as e:
            logging.warning(f"[INFO] Не удалось удалить предыдущее сообщение: {e}")

    await asyncio.sleep(0.1)

    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{text}\n\n⬅️ Возврат в админ-панель:",
        reply_markup=get_admin_panel_keyboard()
    )

    context.user_data["last_bot_message_id"] = msg.message_id
