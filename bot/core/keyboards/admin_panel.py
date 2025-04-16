"""
admin_panel.py

Генератор клавиатуры для административной панели Telegram-бота.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру с основными разделами админ-панели.

    Returns:
        InlineKeyboardMarkup: Клавиатура для администратора.
    """
    keyboard = [
        [
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats_speed"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📨 Обратная связь", callback_data="admin_feedback"),
            InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


def get_speed_stats_period_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора периода для отображения статистики по скорости ответа.

    Returns:
        InlineKeyboardMarkup: Клавиши выбора периода.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 За последний час", callback_data="admin_stats_speed_hour"),
            InlineKeyboardButton("📆 За день", callback_data="admin_stats_speed_day"),
        ],
        [
            InlineKeyboardButton("🕰️ Всё время", callback_data="admin_stats_speed_all"),
            InlineKeyboardButton("🔙 Назад", callback_data="admin_stats"),
        ]
    ])