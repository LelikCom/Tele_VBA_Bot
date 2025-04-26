"""
register_handlers.py
"""

# ───────── Telegram EXT ─────────
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# ───── Эксперимент DeepSeek ─────
from deepseek.utils import is_deepseek_available
from deepseek.experimental_flow import (
    start_experimental_flow,
    cancel_experimental,
    experimental_text_handler,
    retry_experimental,
)

# ───── Авторизация / роли ─────
from bot.core.auth_user.handle_contact import handle_contact
from bot.core.auth_user.handle_admin_pre_auth import handle_pre_auth_user_select
from bot.core.auth_user.handle_admin_role_change import (
    handle_user_role_change_request,
    handle_role_change_confirmation,
    handle_confirm_role_change,
)
from bot.core.auth_user.handle_auth_callback import handle_auth_callback

# ────────── Общий UI ───────────
from bot.commands.start import start
from bot.commands.other_commands import (
    handle_button_click,
    handle_filter_role,
    handle_show_more_users,
)
from bot.core.handlers_for_all.other_handler import (
    get_all_users,
    handle_back_to_roles,
    feedback_entry,
)

# ──────── Админ-панель ─────────
from bot.core.handlers_admin.entry import get_admin_handlers

# ─── Пост-обработка / сценарии ─
from bot.core.handle_all_text import handle_all_text
from macro.filter_rows.handler import process_filter_rows_scenario

# ───────────────────────────────
def register_all_handlers(app: Application) -> None:
    """
    Подключает все хендлеры к Application.

    Args:
        app (Application): Экземпляр Telegram-приложения.
    """
    # ─── Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_users", get_all_users))

    # ─── Админ-панель
    app.add_handlers(get_admin_handlers())

    # ─── Контакт («Поделиться номером»)
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # ─── Callback-кнопки (group=0, порядок важен)
    if is_deepseek_available():
        app.add_handler(CallbackQueryHandler(start_experimental_flow, pattern=r"^experimental_ai$"), group=0)
        app.add_handler(CallbackQueryHandler(cancel_experimental, pattern=r"^back_to_prev$"), group=0)
        app.add_handler(CallbackQueryHandler(retry_experimental, pattern=r"^retry_experimental$"), group=0)

    app.add_handler(CallbackQueryHandler(handle_auth_callback, pattern=r"^auth_"), group=0)
    app.add_handler(CallbackQueryHandler(process_filter_rows_scenario, pattern=r"^(manual|range)"), group=0)
    app.add_handler(CallbackQueryHandler(handle_filter_role, pattern=r"^filter_role_"), group=0)
    app.add_handler(CallbackQueryHandler(handle_back_to_roles, pattern=r"^back_to_roles"), group=0)
    app.add_handler(CallbackQueryHandler(handle_show_more_users, pattern=r"^show_more_"), group=0)
    app.add_handler(CallbackQueryHandler(handle_pre_auth_user_select, pattern=r"^user_select_preauth_"), group=0)
    app.add_handler(CallbackQueryHandler(handle_user_role_change_request, pattern=r"^user_select_"), group=0)
    app.add_handler(CallbackQueryHandler(handle_role_change_confirmation, pattern=r"^change_role_"), group=0)
    app.add_handler(CallbackQueryHandler(handle_confirm_role_change, pattern=r"^confirm_change_"), group=0)
    app.add_handler(CallbackQueryHandler(feedback_entry, pattern=r"^feedback$"), group=0)

    # Универсальный обработчик кнопок — всегда последним в группе 0
    app.add_handler(CallbackQueryHandler(handle_button_click), group=0)

    # ─── Сообщения
    # 1. Основной роутер всех текстов/медиа → group=0
    app.add_handler(
        MessageHandler(
            filters.TEXT
            | filters.PHOTO
            | filters.VIDEO
            | filters.AUDIO
            | filters.ATTACHMENT,
            handle_all_text,
        ),
        group=0,
    )

    # 2. Экспериментальный текст-шаг DeepSeek → group=5
    if is_deepseek_available():
        exp_msg = MessageHandler(filters.TEXT, experimental_text_handler)
        exp_msg.block = False
        app.add_handler(exp_msg, group=5)
