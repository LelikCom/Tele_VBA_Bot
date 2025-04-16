"""
init_app.py

Создаёт и возвращает Telegram Application (бота) с заданным токеном.
"""

import os
from telegram.ext import ApplicationBuilder
from telegram.ext import Defaults


def build_application(post_init=None):
    """
    Строит и возвращает Telegram Application.

    Args:
        post_init (Callable, optional): Функция, вызываемая после инициализации бота.

    Returns:
        Application: Объект Telegram бота.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ Переменная окружения TELEGRAM_BOT_TOKEN не найдена.")

    defaults = Defaults(parse_mode="HTML")

    builder = ApplicationBuilder().token(token).defaults(defaults)

    if post_init:
        builder = builder.post_init(post_init)

    return builder.build()
