import logging
from typing import Optional, List, Tuple
from db.connection import get_db_connection

"""
Модуль для работы с макросами Excel, хранимыми в таблицах vba_unit и vba_formule.
Позволяет загружать макросы по имени и получать списки доступных макросов и формул.
"""


async def fetch_macro_by_name(vba_name: str) -> Optional[str]:
    """
    Возвращает код макроса по его имени.

    Args:
        vba_name (str): Название макроса.

    Returns:
        Optional[str]: Текст макроса или None, если не найден.
    """
    query = "SELECT vba_code FROM vba_unit WHERE vba_name = $1 LIMIT 1"
    try:
        async with get_db_connection() as conn:
            record = await conn.fetchrow(query, vba_name)
            return record['vba_code'] if record else None
    except Exception as e:
        logging.error(f"Ошибка при получении макроса '{vba_name}': {e}")
        return None


async def fetch_all_macros() -> List[Tuple[int, str, str]]:
    """
    Возвращает список всех макросов.

    Returns:
        List[Tuple[int, str, str]]: Список кортежей (id, vba_name, vba_code).
    """
    query = "SELECT id, vba_name, vba_code FROM vba_unit ORDER BY id ASC"
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query)
            return [(r['id'], r['vba_name'], r['vba_code']) for r in records]
    except Exception as e:
        logging.error(f"Ошибка при извлечении всех макросов: {e}")
        return []


async def fetch_formula_by_name(vba_name: str) -> Optional[Tuple[int, str, str, str]]:
    """
    Возвращает формулу по имени.

    Args:
        vba_name (str): Название формулы.

    Returns:
        Optional[Tuple]: Кортеж (id, имя, код, комментарий), либо None.
    """
    query = (
        "SELECT id, vba_formule_name, vba_formule_code, comment_vba_formule "
        "FROM vba_formule WHERE vba_formule_name = $1 LIMIT 1"
    )
    try:
        async with get_db_connection() as conn:
            record = await conn.fetchrow(query, vba_name)
            return (record['id'], record['vba_formule_name'], record['vba_formule_code'], record['comment_vba_formule']) if record else None
    except Exception as e:
        logging.error(f"Ошибка при извлечении формулы '{vba_name}': {e}")
        return None


async def fetch_all_formul_macros() -> List[Tuple[int, str, str, str]]:
    """
    Возвращает список всех формульных макросов из таблицы vba_formule.

    Returns:
        List[Tuple[int, str, str, str]]: Кортежи (id, имя, код, комментарий).
    """
    query = (
        "SELECT id, vba_formule_name, vba_formule_code, comment_vba_formule "
        "FROM vba_formule ORDER BY id ASC"
    )
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query)
            return [
                (r['id'], r['vba_formule_name'], r['vba_formule_code'], r['comment_vba_formule'])
                for r in records
            ]
    except Exception as e:
        logging.error(f"Ошибка при извлечении всех формул: {e}")
        return []
