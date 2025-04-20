import logging
import os


class CustomLogger:
    def __init__(self, log_to_console=True, log_to_file=True, log_file="app.log", log_level=logging.DEBUG, log_dir="logs", prefix=""):
        """
        Инициализация кастомного логгера с возможностью задать уровень и префикс.

        Args:
            log_to_console (bool): Выводить ли логи в консоль.
            log_to_file (bool): Сохранять ли логи в файл.
            log_file (str): Путь к файлу логов.
            log_level (int): Уровень логирования.
            log_dir (str): Директория для хранения логов.
            prefix (str): Приставка для логов.
        """
        if log_to_file and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        log_format = '%(asctime)s [%(levelname)s] %(message)s'
        formatter = logging.Formatter(log_format)

        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if log_to_file:
            file_handler = logging.FileHandler(os.path.join(log_dir, log_file))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.prefix = prefix

    def _log_with_prefix(self, level, message):
        """Добавляет префикс и вызывает стандартное логирование"""
        if self.prefix:
            message = f"[{self.prefix}] {message}"
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)

    def debug(self, message):
        self._log_with_prefix(logging.DEBUG, message)

    def info(self, message):
        self._log_with_prefix(logging.INFO, message)

    def warning(self, message):
        self._log_with_prefix(logging.WARNING, message)

    def error(self, message):
        self._log_with_prefix(logging.ERROR, message)

    def critical(self, message):
        self._log_with_prefix(logging.CRITICAL, message)
