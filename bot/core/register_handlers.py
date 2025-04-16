"""
register_handlers.py

Регистрирует все хендлеры Telegram-бота, включая:
- командные
- callback-кнопки
- обработку сообщений
"""

from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Application,
    filters,
)

from bot.core.auth_user.handle_contact import handle_contact
from bot.core.auth_user.handle_admin_pre_auth import (
    handle_pre_auth_user_select,
)

from bot.core.auth_user.handle_admin_role_change import (
    handle_user_role_change_request,
    handle_role_change_confirmation,
    handle_confirm_role_change,
)

# 🔹 Хендлеры авторизации
from bot.core.auth_user.handle_auth_callback import handle_auth_callback
from bot.core.auth_user.handle_contact import handle_contact

# 🔹 Хендлеры общего интерфейса
from bot.commands.start import (
    start,
)

from bot.commands.other_commands import (
    handle_button_click,
    handle_filter_role,
    handle_show_more_users,
)
from bot.core.handlers_for_all.other_handler import(
    get_all_users,
    handle_back_to_roles,
    feedback_entry,
)

# 🔹 Обработчики админ-панели
from bot.core.handlers_admin.entry import get_admin_handlers

# 🔹 Логика постобработки сообщений
from bot.core.handle_all_text import handle_all_text

# 🔹 Спец-сценарии
from macro.filter_rows.handler import process_filter_rows_scenario


def register_all_handlers(app: Application) -> None:
    """
    Регистрирует все хендлеры в переданном Application.

    Args:
        app (Application): Объект Telegram-приложения.
    """
    # 🔹 Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_users", get_all_users))

    # 🔹 Админские кнопки
    app.add_handlers(get_admin_handlers())

    # 🔹 Контакт
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # 🔹 Callback-кнопки
    app.add_handler(CallbackQueryHandler(handle_auth_callback, pattern="^auth_"))
    app.add_handler(CallbackQueryHandler(process_filter_rows_scenario, pattern="^(manual|range)"))
    app.add_handler(CallbackQueryHandler(handle_filter_role, pattern="^filter_role_"))
    app.add_handler(CallbackQueryHandler(handle_back_to_roles, pattern="^back_to_roles"))
    app.add_handler(CallbackQueryHandler(handle_show_more_users, pattern="^show_more_"))
    app.add_handler(CallbackQueryHandler(handle_pre_auth_user_select, pattern="^user_select_preauth_"))
    app.add_handler(CallbackQueryHandler(handle_user_role_change_request, pattern="^user_select_"))
    app.add_handler(CallbackQueryHandler(handle_role_change_confirmation, pattern="^change_role_"))
    app.add_handler(CallbackQueryHandler(handle_confirm_role_change, pattern="^confirm_change_"))
    app.add_handler(CallbackQueryHandler(feedback_entry, pattern="^feedback$"))

    # 🔹 Остальные кнопки
    app.add_handler(CallbackQueryHandler(handle_button_click))

    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.ATTACHMENT,
            handle_all_text
        )
    )
