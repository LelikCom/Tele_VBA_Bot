import logging
from os import getenv

from dotenv import load_dotenv
from telegram.ext import Application, JobQueue

from db.connection import init_db_pool, close_db_pool
from db.initialize_db import create_tables, populate_initial_data
from bot.core.register_handlers import register_all_handlers
from bot.core.utils.setup_logger import setup_logger
from bot.core.init_app import build_application
from bot.core.role_monitor import role_monitor


async def bot_post_init(application: Application) -> None:
    """Асинхронная инициализация, выполняемая **внутри** event‑loop PTB.

    1. Инициализируем пул БД и создаём/заполняем таблицы.
    2. Регистрируем корутину для фонов задачи мониторинга ролей, которая будет запускаться при старте.
    3. Регистрируем корутину для закрытия пула при выключении бота.
    """
    # 1️⃣  База данных
    await init_db_pool()
    await create_tables()
    await populate_initial_data()

    # 2️⃣  Закрытие пула при Shutdown
    async def _on_shutdown(app: Application) -> None:
        await close_db_pool()
    application.post_shutdown = _on_shutdown


def main() -> None:
    """Синхронная точка входа.

    * Настроить окружение и логгер.
    * Проверить токен.
    * Создать `Application` с `bot_post_init`.
    * Зарегистрировать хендлеры.
    * Запустить polling **без** дополнительного `asyncio.run` –
      `run_polling()` сам управляет event‑loop.
    """
    # 🔧 .env и логгер
    load_dotenv()
    setup_logger()

    # 🔑 Проверка токена
    token = getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN не задан в .env файле.")

    # 🤖 Создание приложения
    application: Application = build_application(post_init=bot_post_init)

    # 📌 Регистрация хендлеров и команд
    register_all_handlers(application)

    # 📌 Запуск задачи мониторинга ролей с использованием job_queue
    application.job_queue.run_once(lambda _: application.create_task(role_monitor(application.bot)), 0)

    logging.info("🤖 Бот запущен через polling.")
    application.run_polling()


if __name__ == "__main__":
    main()
