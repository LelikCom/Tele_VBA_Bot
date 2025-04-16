"""
state.py

Функции для управления состоянием сценария фильтрации строк через context.user_data.
"""

from typing import Any


def set_step(user_data: dict, step: str) -> None:
    """
    Устанавливает текущий шаг сценария.

    Args:
        user_data (dict): Словарь состояния пользователя.
        step (str): Название текущего шага.
    """
    user_data["macro_step"] = step


def get_step(user_data: dict) -> str:
    """
    Возвращает текущий шаг сценария.

    Args:
        user_data (dict): Словарь состояния пользователя.

    Returns:
        str: Название шага (по умолчанию 'ask_column').
    """
    return user_data.get("macro_step", "ask_column")


def set_value(user_data: dict, key: str, value: Any) -> None:
    """
    Устанавливает значение по ключу.

    Args:
        user_data (dict): Словарь состояния.
        key (str): Название поля.
        value (Any): Значение.
    """
    user_data[key] = value


def get_value(user_data: dict, key: str) -> Any:
    """
    Получает значение по ключу.

    Args:
        user_data (dict): Словарь состояния.
        key (str): Название поля.

    Returns:
        Any: Значение или None.
    """
    return user_data.get(key)


def has_keys(user_data: dict, *keys: str) -> bool:
    """
    Проверяет наличие всех указанных ключей.

    Args:
        user_data (dict): Словарь состояния.
        *keys (str): Список ключей.

    Returns:
        bool: True, если все ключи есть.
    """
    return all(k in user_data for k in keys)


def clear_state(user_data: dict) -> None:
    """
    Очищает всё состояние пользователя.

    Args:
        user_data (dict): Словарь состояния.
    """
    user_data.clear()
