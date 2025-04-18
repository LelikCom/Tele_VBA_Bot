"""
Модуль для асинхронного управления соединением к PostgreSQL через asyncpg.
Содержит функции инициализации пула, получения и закрытия соединений.
"""

import logging
import asyncpg
from .db_config import DB_SETTINGS, get_working_host

__all__ = ("init_db_pool", "close_db_pool", "get_db_connection")

_db_pool: asyncpg.pool.Pool | None = None


async def init_db_pool(min_size: int = 1, max_size: int = 10) -> None:
    """
    Инициализирует глобальный пул соединений к базе данных PostgreSQL.

    Args:
        min_size (int): Минимальное число соединений в пуле (по умолчанию 1).
        max_size (int): Максимальное число соединений в пуле (по умолчанию 10).

    Raises:
        asyncpg.PostgresError: В случае ошибки при создании пула.
    """
    global _db_pool
    if _db_pool is None:
        host = get_working_host()
        settings = {**DB_SETTINGS, "host": host}
        if "dbname" in settings:
            settings["database"] = settings.pop("dbname")
        try:
            _db_pool = await asyncpg.create_pool(
                **settings,
                min_size=min_size,
                max_size=max_size,
            )
            logging.info(f"AsyncPG pool initialized on host={host}")
        except Exception as e:
            logging.critical(f"Не удалось инициализировать пул БД: {e}")
            raise


async def close_db_pool() -> None:
    """
    Закрывает ранее инициализированный пул соединений.

    Raises:
        asyncpg.PostgresError: Если при закрытии пула произошла ошибка.
    """
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        logging.info("AsyncPG pool closed")
        _db_pool = None


def get_db_connection() -> asyncpg.pool.PoolAcquireContext:
    """
    Возвращает контекстный менеджер для работы с одним соединением из пула.

    Usage:
        async with get_db_connection() as conn:
            await conn.execute(...)

    Returns:
        asyncpg.pool.PoolAcquireContext: Контекст, дающий asyncpg.Connection.

    Raises:
        RuntimeError: Если пул еще не инициализирован.
    """
    global _db_pool
    if _db_pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db_pool() first.")
    return _db_pool.acquire()
