"""
sql_tools.py

Модуль админ-панели для SQL-запросов:
- Выбор таблицы
- Просмотр всех строк
- Показ полей таблицы
- Экспорт в Excel
"""

import textwrap
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from os import getenv
from dotenv import load_dotenv

from db.users import get_user_role
from db.admins import (
    get_all_table_names,
    get_table_columns,
    execute_custom_sql_query,
    df_to_excel_bytes,
)
from bot.core.utils.sql_utils import reply_with_log
from log_dialog.models_daig import Point


load_dotenv()
ADMIN_CHAT_ID = int(getenv("ADMIN_CHAT_ID", "0"))

async def handle_sql_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Точка входа в SQL-раздел. Предлагает выбрать таблицу.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    user_id = update.effective_user.id
    user_role = await get_user_role(user_id)

    if user_role != "admin":
        return await reply_with_log(
            update,
            context,
            "🔧 Раздел SQL-запросов доступен только администраторам",
            point=Point.SQL,
        )

    context.user_data.clear()
    context.user_data["state"] = "sql:choose_table"

    table_names = await get_all_table_names(user_id)
    if not table_names:
        return await update.effective_message.reply_text("⚠️ Нет доступных таблиц в базе данных.")

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(table, callback_data=f"sql_table_{table}")
        ] for table in table_names])

    await update.effective_message.reply_text(
        "📊 Выберите таблицу для просмотра и SQL-запросов:",
        reply_markup=keyboard
    )


async def handle_sql_table_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    При выборе таблицы показывает её поля и предлагает действия.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    query = update.callback_query
    await query.answer()

    table = query.data.replace("sql_table_", "")
    context.user_data["sql_table"] = table
    context.user_data["state"] = "sql:waiting_query"

    try:
        columns = await get_table_columns(table)
    except Exception as e:
        logging.error(f"Ошибка получения колонок таблицы '{table}': {e}")
        return await query.message.reply_text(f"❌ Не удалось получить поля таблицы:\n{e}")

    if not columns:
        return await query.message.reply_text("⚠️ У таблицы нет видимых полей.")

    field_list = "\n".join([f"• <code>{name}</code>: <i>{dtype}</i>" for name, dtype in columns])

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Показать все данные (ALL)", callback_data=f"sql_all_{table}")],
        [InlineKeyboardButton("✏️ Ввести свой SQL-запрос", callback_data="sql_custom_query")]
    ])

    await query.message.edit_text(
        f"📄 <b>Таблица:</b> <code>{table}</code>\n\n"
        f"<b>Поля:</b>\n{field_list}\n\n"
        f"Выберите действие ниже или введите свой SQL-запрос вручную.",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def handle_sql_all_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Выполняет SELECT * FROM table и отправляет как текст или Excel-файл.

    Args:
        update (Update): Объект Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    query = update.callback_query
    await query.answer()

    table = query.data.replace("sql_all_", "")
    sql = f"SELECT * FROM {table}"

    try:
        df = await execute_custom_sql_query(sql, user_id=ADMIN_CHAT_ID)
    except Exception as e:
        logging.error(f"Ошибка при выполнении SQL-запроса: {e}")
        return await query.message.reply_text(
            f"❌ Ошибка при выполнении запроса:\n<code>{e}</code>",
            parse_mode=ParseMode.HTML
        )

    if df.empty:
        return await query.message.reply_text("⚠️ Таблица пуста.")

    # Если таблица маленькая, отправляем текст
    if len(df) <= 10 and df.shape[1] <= 5:
        text = df.to_string(index=False)
        # Ограничиваем длину текста, если он слишком большой
        max_length = 4096
        if len(text) > max_length:
            text = textwrap.fill(text, max_length)  # Разбиваем текст на несколько частей

        return await query.message.reply_text(
            f"📥 Результат:\n<pre>{text}</pre>",
            parse_mode=ParseMode.HTML
        )

    # Если таблица большая, отправляем Excel
    excel_buf = df_to_excel_bytes(df)
    await query.message.reply_document(
        document=InputFile(excel_buf, f"{table}.xlsx"),
        caption=f"📎 Все строки из таблицы <b>{table}</b>",
        parse_mode=ParseMode.HTML
    )

    # Очищаем состояние пользователя
    context.user_data.pop("state", None)
    context.user_data.pop("sql_table", None)
