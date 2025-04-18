"""
admins.py

Модуль для административных действий с базой данных PostgreSQL.
Содержит функции:
- Просмотр таблиц и колонок
- Выполнение произвольных SQL-запросов
- Экспорт результата в Excel
"""

import logging
from typing import List, Tuple
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

from db.connection import get_db_connection


async def get_all_table_names() -> List[str]:
    """
    Возвращает список всех таблиц в схеме `public`.

    Returns:
        List[str]: Список названий таблиц.
    """
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query)
            return [r['table_name'] for r in records]
    except Exception as e:
        logging.error(f"Не удалось получить список таблиц: {e}")
        return []


async def get_table_columns(table: str) -> List[Tuple[str, str]]:
    """
    Возвращает список колонок таблицы с их типами.

    Args:
        table (str): Название таблицы.

    Returns:
        List[Tuple[str, str]]: Кортежи (имя колонки, тип данных).
    """
    query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = $1
        ORDER BY ordinal_position
    """
    try:
        async with get_db_connection() as conn:
            records = await conn.fetch(query, table)
            return [(r['column_name'], r['data_type']) for r in records]
    except Exception as e:
        logging.error(f"Не удалось получить колонки таблицы '{table}': {e}")
        return []


async def execute_custom_sql_query(query: str) -> pd.DataFrame:
    """
    Выполняет произвольный SQL-запрос и возвращает результат как DataFrame.

    Args:
        query (str): SQL-запрос (желательно SELECT).

    Returns:
        pd.DataFrame: Результат запроса. Если запрос не возвращает данных — пустой DataFrame.
    """
    try:
        async with get_db_connection() as conn:
            sql = query.strip().lower()
            if sql.startswith('select'):
                records = await conn.fetch(query)
                if records:
                    columns = list(records[0].keys())
                    data = [tuple(r) for r in records]
                    return pd.DataFrame(data, columns=columns)
                else:
                    return pd.DataFrame()
            else:
                await conn.execute(query)
                return pd.DataFrame()
    except Exception as e:
        logging.error(f"Ошибка выполнения SQL-запроса: {e}")
        return pd.DataFrame()


def df_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    """
    Преобразует DataFrame в Excel-файл и возвращает его в виде байтового потока.

    Args:
        df (pd.DataFrame): Табличные данные.

    Returns:
        BytesIO: Поток с Excel-файлом.
    """
    wb = Workbook()
    ws = wb.active

    # Заголовки
    for col_num, column in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_num, value=column)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Данные
    for row_num, row in enumerate(df.itertuples(index=False), 2):
        for col_num, value in enumerate(row, 1):
            val = str(value)
            if len(val) > 40:
                val = val[:40]
            cell = ws.cell(row=row_num, column=col_num, value=val)
            cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

    # Автоширина
    for col_num, column in enumerate(df.columns, 1):
        col_letter = get_column_letter(col_num)
        max_len = max(
            [len(str(df.columns[col_num - 1]))]
            + [len(str(val)) for val in df.iloc[:, col_num - 1].astype(str).values]
        )
        ws.column_dimensions[col_letter].width = min(max_len + 2, 40)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

