"""
handlers.py

Обработка всех текстовых сообщений и сценариев:
- Ответы администратора на отзывы.
- Обработка SQL-запросов от администраторов.
- Обработка активных сценариев (макросы, фильтрация, преобразование данных).
- Отправка шутки дня и общая обработка сообщений.
"""

import logging
import psycopg2
from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.feedback import fetch_feedback_by_id
from db.admins import execute_custom_sql_query, df_to_excel_bytes
from bot.feedback.router import feedback_router
from macro.filter_rows.handler import process_filter_rows_scenario
from macro.convert_to_num.handler import process_convert_column_scenario
from bot.core.utils.admin_utils import is_admin
from bot.core.handlers_admin.broadcast import (
    handle_broadcast_datetime,
    handle_broadcast_whats_new,
)


async def handle_all_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Универсальный обработчик всех текстовых сообщений Telegram.
    Порядок:
        0. Если активен экспериментальный режим DeepSeek — пропускаем
        1. Ответ на отзыв
        2. SQL-запросы админов
        3. Активные сценарии (макросы, рассылка, feedback)
        4. Шутка дня
        5. Fallback
    """
    user_data = context.user_data

    # ────────────────────────────────────────────────────────────
    # 0. Эксперимент «Попробовать с ИИ»
    # ────────────────────────────────────────────────────────────
    if user_data.get("awaiting_experimental_prompt"):
        # Пусть обработает experimental_text_handler
        return

    # ────────────────────────────────────────────────────────────
    # 1. Ответ администратора на отзыв
    # ────────────────────────────────────────────────────────────
    if "reply_feedback" in user_data:
        data = user_data.pop("reply_feedback")
        target_user_id = data["user_id"]
        reply_text = update.message.text

        theme_text = ""
        fid = data.get("fid")
        if fid:
            row = await fetch_feedback_by_id(fid)
            if row:
                theme = row[2] or "(не указана)"
                theme_text = f"📝 Тема: {theme}\n\n"

        final_message = f"{theme_text}Ответ на отзыв от администратора:\n\n{reply_text}"

        try:
            await context.bot.send_message(chat_id=target_user_id, text=final_message)
            await update.message.reply_text("✅ Ответ отправлен пользователю.")
        except Exception as e:
            await update.message.reply_text(f"❌ Не удалось отправить сообщение: {e}")
        return

    # ────────────────────────────────────────────────────────────
    # 2. SQL-запросы админов
    # ────────────────────────────────────────────────────────────
    state = user_data.get("state")
    if state == "sql:waiting_query":
        user_id = update.effective_user.id

        if not await is_admin(user_id):
            await update.message.reply_text("⛔ У вас нет доступа к SQL.")
            return

        query_text = update.message.text.strip()
        table_name = user_data.get("sql_table")
        if table_name and "table" in query_text.lower():
            query_text = query_text.replace("table", table_name)

        try:
            df = await execute_custom_sql_query(query_text, user_id)
        except psycopg2.Error as e:
            msg = e.pgerror or str(e)
            return await update.message.reply_text(
                f"❌ Ошибка SQL:\n<code>{msg.strip()}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            return await update.message.reply_text(
                f"❌ Неизвестная ошибка:\n<code>{str(e)}</code>",
                parse_mode=ParseMode.HTML,
            )

        if df.empty:
            return await update.message.reply_text("⚠️ Запрос выполнен, но результат пуст.")

        if len(df) <= 10 and df.shape[1] <= 5:
            text = df.to_string(index=False)
            await update.message.reply_text(
                f"✅ Запрос выполнен:\n<pre>{text}</pre>", parse_mode=ParseMode.HTML
            )
        else:
            excel_buf = df_to_excel_bytes(df)
            await update.message.reply_document(
                document=InputFile(excel_buf, "result.xlsx"),
                caption="📎 Результат запроса (Excel)",
            )

        user_data.pop("state", None)
        user_data.pop("sql_table", None)
        return

    # ────────────────────────────────────────────────────────────
    # 3. Активные сценарии макросов / рассылок / feedback
    # ────────────────────────────────────────────────────────────
    macro_step = user_data.get("macro_step")
    if state == "broadcast:datetime":
        await handle_broadcast_datetime(update, context)
        return

    if state == "broadcast:whats_new":
        await handle_broadcast_whats_new(update, context)
        return

    if state and state.startswith("feedback:"):
        await feedback_router(update, context)
        return

    filter_steps = {
        "ask_column", "process_column", "ask_mode", "wait_for_mode",
        "ask_manual_values", "process_manual_values", "ask_sheet_range",
        "process_range_input", "ask_sheet_name", "process_sheet_name",
        "confirm_macro", "show_instruction",
    }
    if macro_step in filter_steps:
        await process_filter_rows_scenario(update, context)
        return

    convert_steps = {"ask_column", "ask_column_waiting", "ask_start_cell"}
    if macro_step in convert_steps:
        await process_convert_column_scenario(update, context)
        return

    # ────────────────────────────────────────────────────────────
    # 4. Шутка дня
    # ────────────────────────────────────────────────────────────
    if update.message and update.message.text:
        text = update.message.text.strip().lower()
        if user_data.get("joke_waiting") and text in {"кто там", "кто там?"}:
            user_data["joke_waiting"] = False
            await update.message.reply_text("Aiogram.")
            return

    # ────────────────────────────────────────────────────────────
    # 5. Fallback
    # ────────────────────────────────────────────────────────────
    logging.info("[ROUTER] Нет активного сценария — ответ по умолчанию")
    if update.message:
        await update.message.reply_text("❓ Я не понял. Попробуй /start.")
