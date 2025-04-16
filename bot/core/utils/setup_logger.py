"""
logger.py

Настройка логирования для приложения:
- Логи выводятся в консоль и сохраняются в файл.
- Настройка уровня логирования для консольного вывода и сохранения в файл.
"""

import logging
import os
import sys


def setup_logger():
    """
    Настраивает глобальный логгер приложения.

    Логи пишутся в файл `logs/bot.log` и выводятся в консоль с помощью двух хендлеров:
    - Один для консоли, выводящий логи на экран.
    - Один для файла, записывающий логи в указанный файл.

    Также настраивается уровень логирования для некоторых популярных библиотек,
    таких как `httpx`, `apscheduler`, и `telegram`, с уровнем логирования `WARNING`,
    чтобы подавить лишний шум.

    Returns:
        None: Функция ничего не возвращает, но настраивает логирование.
    """
    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    log_file_path = "logs/bot.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Очистим предыдущие хендлеры (если перезапуск)
    root_logger.handlers.clear()

    # Консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # Файл
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

    # Подавим лишний шум
    for noisy in ("httpx", "apscheduler", "telegram"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.info("📋 Логгер инициализирован.")

