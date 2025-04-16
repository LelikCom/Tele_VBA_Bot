"""
macros.py

Модуль для работы с макросами Excel, хранимыми в таблицах vba_unit и vba_formule.
Позволяет загружать макросы по имени и получать списки доступных макросов и формул.
"""

import logging
from typing import Optional, List, Tuple
from db.connection import connect_db
from telegram.helpers import escape_markdown


def fetch_macro_by_name(vba_name: str) -> Optional[str]:
    """
    Возвращает код макроса по его имени.

    Args:
        vba_name (str): Название макроса.

    Returns:
        Optional[str]: Текст макроса или None, если не найден.
    """
    query = "SELECT vba_code FROM vba_unit WHERE vba_name = %s LIMIT 1"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (vba_name,))
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        logging.error(f"Ошибка при получении макроса '{vba_name}': {e}")
        return None


def fetch_all_macros() -> List[Tuple[int, str, str]]:
    """
    Возвращает список всех макросов.

    Returns:
        List[Tuple[int, str, str]]: Список кортежей (id, vba_name, vba_code).
    """
    query = "SELECT id, vba_name, vba_code FROM vba_unit ORDER BY id ASC"
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при извлечении всех макросов: {e}")
        return []


def fetch_formula_by_name(vba_name: str) -> Optional[Tuple[int, str, str, str]]:
    """
    Возвращает формулу по имени.

    Args:
        vba_name (str): Название формулы.

    Returns:
        Optional[Tuple]: Кортеж (id, имя, код, комментарий), либо None.
    """
    query = """
        SELECT id, vba_formule_name, vba_formule_code, comment_vba_formule
        FROM vba_formule
        WHERE vba_formule_name = %s
        LIMIT 1
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (vba_name,))
                return cur.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при извлечении формулы '{vba_name}': {e}")
        return None


def fetch_all_formul_macros() -> List[Tuple[int, str, str, str]]:
    """
    Возвращает список всех формульных макросов из таблицы vba_formule.

    Returns:
        List[Tuple[int, str, str, str]]: Кортежи (id, имя, код, комментарий).
    """
    query = """
        SELECT id, vba_formule_name, vba_formule_code, comment_vba_formule
        FROM vba_formule
        ORDER BY id ASC
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при извлечении всех формул: {e}")
        return []
