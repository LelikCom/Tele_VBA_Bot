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

from db.connection import connect_db


def get_all_table_names() -> List[str]:
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
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Не удалось получить список таблиц: {e}")
        return []


def get_table_columns(table: str) -> List[Tuple[str, str]]:
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
        WHERE table_name = %s
        ORDER BY ordinal_position
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table,))
                return cur.fetchall()
    except Exception as e:
        logging.error(f"Не удалось получить колонки таблицы '{table}': {e}")
        return []


def execute_custom_sql_query(query: str) -> pd.DataFrame:
    """
    Выполняет произвольный SQL-запрос и возвращает результат как DataFrame.

    Args:
        query (str): SQL-запрос (желательно SELECT).

    Returns:
        pd.DataFrame: Результат запроса. Если запрос не возвращает данных — пустой DataFrame.
    """
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            if cur.description is not None:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=columns)
            else:
                conn.commit()
                return pd.DataFrame()
    except Exception as e:
        logging.error(f"Ошибка выполнения SQL-запроса: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


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
