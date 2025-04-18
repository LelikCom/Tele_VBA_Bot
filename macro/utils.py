"""
utils.py

Утилиты для сценария фильтрации строк:
- Проверка форматов ячеек и диапазонов
- Экранирование MarkdownV2
- Универсальная отправка сообщений
"""

import re
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, Message
from telegram.constants import ParseMode


RANGE_PATTERN = re.compile(
    r"^([A-Za-zА-Яа-яЁё0-9_]+!)?[A-ZА-Я]+\d+(:[A-ZА-Я]+\d+)?$",
    re.IGNORECASE
)


def split_cell(cell: str):
    """
    Делит ячейку (например, A10) на буквы и цифры: ('A', 10)
    """
    match = re.match(r"^([A-Z]+)(\d+)$", cell)
    if not match:
        raise ValueError(f"Не удалось распознать ячейку: {cell}")
    return match.group(1), match.group(2)


def escape_markdown(text: str) -> str:
    """Экранирование специальных символов MarkdownV2"""
    escape_chars = r'_*\[\]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы MarkdownV2 для безопасного отображения текста.

    Args:
        text (str): Текст для экранирования.

    Returns:
        str: Экранированный текст.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return ''.join(f"\\{char}" if char in escape_chars else char for char in text)


def validate_cell(cell: str) -> bool:
    """
    Проверяет, корректна ли ячейка (поддерживает буквенно-числовой формат).

    Args:
        cell (str): Строка с адресом ячейки (например, 'A1').

    Returns:
        bool: True если ячейка корректна, иначе False.
    """
    return re.match(r'^[A-ZА-Я]+\d+$', cell, re.IGNORECASE) is not None


async def send_response(
    update: Update,
    text: str,
    keyboard: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = ParseMode.HTML
) -> Message:
    """
    Универсальная отправка сообщений пользователю (поддержка обычных и callback сообщений).

    Args:
        update (Update): Объект Telegram обновления.
        text (str): Текст сообщения.
        keyboard (InlineKeyboardMarkup, optional): Кнопки под сообщением.
        parse_mode (str): Режим форматирования (по умолчанию HTML).

    Returns:
        Message: Отправленное сообщение.
    """
    if update.callback_query:
        await update.callback_query.answer()
        return await update.callback_query.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
    return await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=parse_mode
    )


def parse_column(input_value: str) -> int | None:
    """
    Преобразует буквенное обозначение столбца в номер или возвращает номер как есть.

    Аргументы:
        input_value (str): Введенное пользователем значение (буква или номер).

    Возвращает:
        int | None: Номер столбца, если успешно, иначе None.
    """
    input_value = input_value.strip().upper()

    # Если это число, возвращаем его как номер столбца
    if input_value.isdigit():
        return int(input_value)

    # Проверка, является ли строка буквенным обозначением столбца
    if re.fullmatch(r"[A-Z]+", input_value):
        result = 0
        for char in input_value:
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result

    return None


def format_comment_bold_before_dash(comment: str) -> str:
    """
    Делает жирной часть до первого '–' или ':', без экранирования.
    Используется с ParseMode.MARKDOWN.
    """
    lines = comment.strip().splitlines()
    formatted = []

    for line in lines:
        if "–" in line:
            key, value = line.split("–", 1)
            formatted.append(f"*{key.strip()}* – {value.strip()}")
        elif ":" in line:
            key, value = line.split(":", 1)
            formatted.append(f"*{key.strip()}* : {value.strip()}")
        else:
            formatted.append(line.strip())
    return "\n".join(formatted)


def reset_macro_state(context):
    """
    Очищает состояние, связанное с макросами, из context.user_data.

    Удаляет все ключи, относящиеся к текущему сценарию работы с макросами.

    Args:
        context: Контекст Telegram-бота, содержащий user_data.
    """
    keys_to_clear = [
        "macro_step", "instruction_type", "current_macro_name",
        "column_num", "start_cell", "mode", "values", "sheet", "range"
    ]
    for key in keys_to_clear:
        context.user_data.pop(key, None)

