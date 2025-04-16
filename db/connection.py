"""
connection.py

Модуль для создания подключения к базе данных PostgreSQL.
Использует настройки из db_config.py.
"""

import logging
import psycopg2
from .db_config import DB_SETTINGS


def connect_db():
    """
    Устанавливает соединение с базой данных PostgreSQL,
    используя параметры из DB_SETTINGS.

    Returns:
        connection (psycopg2.extensions.connection): Объект подключения к базе данных.

    Raises:
        psycopg2.Error: В случае ошибки при подключении.
    """
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        conn.set_client_encoding("UTF8")
        return conn
    except psycopg2.Error as e:
        logging.critical(f"Не удалось подключиться к базе данных: {e}")
        raise
