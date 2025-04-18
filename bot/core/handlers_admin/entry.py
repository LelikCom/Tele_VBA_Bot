"""
entry.py

Точка входа: собирает все хендлеры для админ-панели Telegram-бота
и команду /admin.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from bot.core.utils.admin_utils import is_admin
from bot.core.keyboards.admin_panel import get_admin_panel_keyboard

# ===== Хендлеры по функциональным модулям =====
from bot.core.handlers_admin.panel import show_admin_panel
from bot.core.handlers_admin.broadcast import (
    admin_broadcast_entry,
    handle_broadcast_choose_role,
    handle_broadcast_confirm,
    handle_broadcast_cancel,
)
from bot.core.handlers_admin.feedback import (
    show_feedback_list,
    handle_feedback_next,
    show_feedback_item,
    handle_feedback_reply_start,
)
from bot.core.handlers_admin.stats import (
    handle_admin_speed_entry,
    handle_admin_speed_stats,
)
from bot.core.handlers_admin.users import handle_admin_users
from bot.core.handlers_admin.sql_tools import (
    handle_sql_entry,
    handle_sql_table_select,
    handle_sql_all_query,
)


def get_admin_handlers() -> list[CallbackQueryHandler]:
    """
    Возвращает список всех CallbackQueryHandler-ов для административных действий.

    Этот список хендлеров обрабатывает различные команды, связанные с администрированием, такими как
    показ панели администратора, обработка статистики, управление пользователями, обратная связь, рассылка и SQL-запросы.

    Returns:
        list[CallbackQueryHandler]: Список хендлеров, которые обрабатывают административные команды.
    """
    return [
        # Панель
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),

        # Статистика
        CallbackQueryHandler(handle_admin_speed_entry, pattern="^admin_stats_speed$"),
        CallbackQueryHandler(handle_admin_speed_stats, pattern="^admin_stats_speed_(hour|day|all)$"),

        # Пользователи
        CallbackQueryHandler(handle_admin_users, pattern="^admin_users$"),

        # Обратная связь
        CallbackQueryHandler(show_feedback_list, pattern="^admin_feedback$"),
        CallbackQueryHandler(handle_feedback_next, pattern="^feedback_next$"),
        CallbackQueryHandler(show_feedback_item, pattern=r"^show_feedback_\d+$"),
        CallbackQueryHandler(handle_feedback_reply_start, pattern=r"^reply_feedback_\d+_\d+$"),

        # Рассылка
        CallbackQueryHandler(admin_broadcast_entry, pattern="^admin_broadcast$"),
        CallbackQueryHandler(handle_broadcast_choose_role, pattern="^broadcast_role_"),
        CallbackQueryHandler(handle_broadcast_confirm, pattern="^broadcast_confirm$"),
        CallbackQueryHandler(handle_broadcast_cancel, pattern="^broadcast_cancel$"),

        # SQL
        CallbackQueryHandler(handle_sql_entry, pattern="^admin_sql$"),
        CallbackQueryHandler(handle_sql_table_select, pattern=r"^sql_table_"),
        CallbackQueryHandler(handle_sql_all_query, pattern=r"^sql_all_"),
    ]


def get_admin_command_handler() -> CommandHandler:
    """
    Хендлер для команды /admin.

    Возвращает хендлер для команды /admin, который запускает панель администратора.

    Returns:
        CommandHandler: Хендлер команды /admin.
    """
    return CommandHandler("admin", cmd_admin)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /admin — открывает панель администратора.

    Эта функция проверяет, является ли пользователь администратором. Если да, то отправляется сообщение с панелью
    администратора, иначе — уведомление о недоступности этой функции.

    Args:
        update (Update): Сообщение Telegram, содержащее информацию о пользователе и его запросе.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий дополнительные данные.

    Returns:
        None: Функция ничего не возвращает, но отправляет сообщения в чат.
    """
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("⛔ У вас нет доступа к админ-панели.")
        return

    await update.message.reply_text(
        "🔧 Добро пожаловать в админ-панель:",
        reply_markup=get_admin_panel_keyboard()
    )



