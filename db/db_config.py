import os
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_SETTINGS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 5432)),
}


def get_working_host() -> str:
    """
    Пробует подключиться к доступным хостам и возвращает первый рабочий.

    Returns:
        str: Рабочий хост (например, 'localhost' или 'postgres_db').

    Raises:
        ConnectionError: Если не удалось подключиться ни к одному хосту.
    """
    # Пробуем сначала localhost, а потом postgres_db
    for host in ["localhost", "postgres_db"]:
        try:
            test_settings = DB_SETTINGS.copy()
            test_settings["host"] = host
            conn = psycopg2.connect(**test_settings)
            conn.close()
            logging.info(f"[DB] Успешное подключение через {host}")
            return host
        except psycopg2.OperationalError:
            logging.warning(f"[DB] {host} недоступен, пробуем другой...")

    raise ConnectionError("❌ Не удалось подключиться ни через localhost, ни через postgres_db")


# Определяем рабочий хост и сразу подставляем его в настройки
try:
    DB_SETTINGS["host"] = get_working_host()
except ConnectionError as e:
    logging.critical(f"[DB] {e}")
    raise
