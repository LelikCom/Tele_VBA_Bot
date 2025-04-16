"""
register_commands.py

Устанавливает Telegram-команды (/start, /get_users и др.)
для разных ролей пользователей.
"""

import logging
from telegram import BotCommand, BotCommandScopeChat
from telegram.ext import Application

from db.users import get_users_by_role


async def setup_commands(app: Application) -> None:
    """
    Устанавливает команды бота для разных ролей.

    Args:
        app (Application): Telegram-приложение.
    """
    logging.info("⚙️ Устанавливаем команды Telegram бота...")

    # Команды по умолчанию (если нет роли)
    await app.bot.set_my_commands([BotCommand("start", "Запустить бота")])

    # Команды по ролям
    role_commands = {
        "admin": [
            BotCommand("start", "Запустить бота"),
            BotCommand("get_users", "📥 Получить список пользователей"),
        ],
        "auth": [
            BotCommand("start", "Запустить бота"),
        ],
        "preauth": [
            BotCommand("start", "Запустить бота"),
        ],
        "noauth": [
            BotCommand("start", "Запустить бота"),
        ],
    }

    for role, commands in role_commands.items():
        user_ids = get_users_by_role(role)
        for user_id in user_ids:
            try:
                await app.bot.set_my_commands(
                    commands=commands,
                    scope=BotCommandScopeChat(user_id)
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось установить команды для {user_id} ({role}): {e}")
