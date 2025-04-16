"""
main.py

Точка входа для запуска Telegram-бота на python-telegram-bot.
"""

import logging
import asyncio
from os import getenv

from db.initialize_db import create_tables, populate_initial_data
from dotenv import load_dotenv
from telegram.ext import Application
from bot.core.register_handlers import register_all_handlers
from bot.core.register_commands import setup_commands
from bot.core.utils.setup_logger import setup_logger
from bot.core.init_app import build_application
from bot.core.role_monitor import role_monitor


async def main():
    # 🔧 Загрузка переменных окружения
    load_dotenv()

    # 📝 Настройка логгера
    setup_logger()

    # 🔑 Проверка токена
    token = getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN не задан в .env файле.")

    # 🗄️ Инициализация базы данных (синхронно)
    create_tables()
    populate_initial_data()

    # 🤖 Создание экземпляра Telegram Application с post_init
    application: Application = build_application(post_init=setup_commands)

    # 📌 Регистрация всех хендлеров
    register_all_handlers(application)

    # 🛠️ Запуск фоновой задачи мониторинга ролей
    asyncio.create_task(role_monitor(application.bot))

    # 🚀 Запуск бота
    logging.info("🤖 Бот запущен через polling.")
    await application.run_polling()


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

