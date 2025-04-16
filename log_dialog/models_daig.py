from enum import Enum


class Point(str, Enum):
    MAIN_MENU = "Главное меню"
    TEXT = "Текст"
    START_ROW = "start_row"
    ERROR = "Ошибка"
    SCENARIO = "Сценарий"
    CONFIRM = "Подтверждение"
    SQL = "SQL"
    JOKE = "Шутка"
    UNKNOWN = "Неизвестно"
    CONTACT = "Контакт"
    COLUMN = "Столбец"
