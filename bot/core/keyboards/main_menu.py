"""
main_menu.py

Модуль для построения инлайн-клавиатур главного меню и макросов.
"""

from typing import List, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db.macros import fetch_all_macros, fetch_all_formul_macros


def create_button_rows(
    items: List[Tuple],
    prefix: str,
    columns: int = 2
) -> List[List[InlineKeyboardButton]]:
    """
    Формирует ряды инлайн-кнопок из списка элементов.

    Args:
        items (List[Tuple]): Список кортежей (id, name, ...).
        prefix (str): Префикс для callback_data (например, "macro").
        columns (int): Количество колонок в ряду.

    Returns:
        List[List[InlineKeyboardButton]]: Разметка кнопок.
    """
    rows = []
    row = []
    for item in items:
        btn = InlineKeyboardButton(
            text=item[1],
            callback_data=f"{prefix}:{item[1]}"
        )
        row.append(btn)
        if len(row) == columns:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def add_back_button(keyboard: List[List[InlineKeyboardButton]]) -> None:
    """
    Добавляет кнопку "⬅️ Назад" в конец клавиатуры.

    Args:
        keyboard (List[List[InlineKeyboardButton]]): Разметка клавиатуры.
    """
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])


def get_main_menu_keyboard(user_role: str) -> InlineKeyboardMarkup:
    """
    Главное меню в зависимости от роли пользователя.

    Args:
        user_role (str): Роль пользователя ('noauth', 'auth', 'admin', 'preauth').

    Returns:
        InlineKeyboardMarkup: Разметка главного меню.
    """
    keyboard = []

    main_buttons = [
        InlineKeyboardButton(text="📝 Формулы", callback_data="formulas"),
        InlineKeyboardButton(text="⚙️ Макросы", callback_data="macros")
    ]

    if user_role == "noauth":
        keyboard.append(main_buttons)
        keyboard.append([
            InlineKeyboardButton(text="🔐 Авторизация", callback_data="authorization")
        ])
    elif user_role == "auth":
        keyboard.append(main_buttons)
        keyboard.append([
            InlineKeyboardButton(text="🗃️ SQL запросы", callback_data="sql_requests"),
            InlineKeyboardButton(text="🎭 Шутка дня", callback_data="joke_of_the_day")
        ])
        keyboard.append([
            InlineKeyboardButton(text="📮 Обратная связь", callback_data="feedback")
        ])
    elif user_role == "admin":
        keyboard.append(main_buttons)
        keyboard.append([
            InlineKeyboardButton(text="🗃️ SQL запросы", callback_data="sql_requests"),
            InlineKeyboardButton(text="🎭 Шутка дня", callback_data="joke_of_the_day"),
            InlineKeyboardButton(text="📮 Обратная связь", callback_data="feedback")
        ])
        keyboard.append([
            InlineKeyboardButton(text="🛠️ Админ-панель", callback_data="admin_panel")
        ])
    elif user_role == "preauth":
        keyboard.append(main_buttons)

    return InlineKeyboardMarkup(keyboard)


def get_macros_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура со списком макросов из базы данных (по 2 в ряд).

    Извлекает все макросы из базы данных и создаёт клавиатуру, где макросы
    располагаются по два в ряд. Также добавляется кнопка "Назад".

    Returns:
        InlineKeyboardMarkup: Инлайн клавиатура с кнопками для макросов.
    """
    macros = fetch_all_macros()
    keyboard = create_button_rows(macros, prefix="macro", columns=2)
    add_back_button(keyboard)
    return InlineKeyboardMarkup(keyboard)


def get_formulas_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура со списком формул из базы данных (по 1 в ряд).

    Извлекает все формулы из базы данных и создаёт клавиатуру, где формулы
    располагаются по одной в ряд. Также добавляется кнопка "Назад".

    Returns:
        InlineKeyboardMarkup: Инлайн клавиатура с кнопками для формул.
    """
    formulas = fetch_all_formul_macros()
    keyboard = create_button_rows(formulas, prefix="formula", columns=1)
    add_back_button(keyboard)
    return InlineKeyboardMarkup(keyboard)


def build_items_keyboard(items: list, prefix: str, columns: int = 1) -> InlineKeyboardMarkup:
    """
    Общая клавиатура по списку элементов + кнопка "Назад".

    Args:
        items (list): Список кортежей (id, name).
        prefix (str): Префикс для callback_data.
        columns (int): Кол-во кнопок в ряду.

    Returns:
        InlineKeyboardMarkup
    """
    keyboard = create_button_rows(items, prefix=prefix, columns=columns)
    add_back_button(keyboard)
    return InlineKeyboardMarkup(keyboard)


def get_instruction_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с вопросом об инструкции.

    Создаёт инлайн клавиатуру с двумя кнопками: одна для подтверждения желания
    увидеть инструкцию, другая — для отказа от её просмотра.

    Returns:
        InlineKeyboardMarkup: Инлайн клавиатура с вопросом об инструкции и кнопками для выбора.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="✅ Да, показать инструкцию", callback_data="instruction_yes"),
            InlineKeyboardButton(text="❌ Нет, спасибо", callback_data="instruction_no")
        ]
    ])


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для админ-панели.

    Создаёт инлайн клавиатуру с кнопками для навигации по админ-панели, включая
    разделы статистики, пользователей, рассылки и отзывов.

    Returns:
        InlineKeyboardMarkup: Инлайн клавиатура для админ-панели с доступными действиями.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🗣 Отзывы", callback_data="admin_feedback")
        ]
    ])

