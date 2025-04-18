"""
handlers.py

Обработка запросов для различных сценариев:
- Выбор формул и макросов
- Инструкции по формам и макросам
- Работа с пользователями (с фильтрацией по ролям)
- Отправка шутки дня
- Обработка запросов на возвращение в главное меню и отказ от инструкций
"""

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from macro.utils import (
    escape_markdown,
    format_comment_bold_before_dash,
)
from db.macros import (
    fetch_all_formul_macros,
    fetch_all_macros,
    fetch_formula_by_name,
)
from db.users import (
    save_user,
    get_user_role,
    get_users_by_role,
    fetch_users_by_role,
)
from bot.core.utils.sql_utils import reply_with_log
from log_dialog.handlers_diag import log_step
from log_dialog.models_daig import Point
from bot.core.keyboards.main_menu import get_main_menu_keyboard
from macro.macros_logic import (
    run_macro_scenario,
    show_instruction_options,
)


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text)
async def handle_formulas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор раздела "Формулы" из главного меню.

    Args:
        update (Update): Объект Telegram-обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Returns:
        Message: Ответное сообщение или отредактированное сообщение с клавиатурой.
    """

    formulas = await fetch_all_formul_macros()

    buttons = [[InlineKeyboardButton(name, callback_data=f"formula:{name}")] for _, name, _, _ in formulas]
    buttons.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")])

    if update.callback_query:
        return await update.callback_query.edit_message_text(
            "📚 Выбери нужную формулу:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        return await update.message.reply_text(
            "📚 Выбери нужную формулу:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text)
async def handle_macros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор раздела "Макросы" из главного меню.

    Загружает все доступные макросы из базы данных и отправляет пользователю список кнопок
    для выбора одного из них, включая кнопку возврата в главное меню.

    Args:
        update (Update): Объект Telegram-обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Returns:
        Message: Сообщение с клавиатурой или отредактированное сообщение, если был callback.
    """
    macros = await fetch_all_macros()
    buttons = [[InlineKeyboardButton(name, callback_data=f"macro:{name}")] for _, name, _ in macros]
    buttons.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")])

    if update.callback_query:
        return await update.callback_query.edit_message_text(
            "⚙️ Выбери нужный макрос:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        return await update.message.reply_text(
            "⚙️ Выбери нужный макрос:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def handle_instruction_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает подтверждение пользователя на просмотр инструкции.

    Отправляет пользователю подробную инструкцию по добавлению формулы или макроса
    в редактор VBA Excel, в зависимости от типа выбранного объекта.

    Args:
        update (Update): Объект Telegram-обновления, содержащий callback-запрос.
        context (ContextTypes.DEFAULT_TYPE): Контекст взаимодействия пользователя с ботом.

    Returns:
        Message: Отправленное сообщение с инструкцией и главной клавиатурой.
    """
    query = update.callback_query
    instruction_type = context.user_data.get("instruction_type", "macro")
    name = context.user_data.get(f"current_{instruction_type}_name", "Неизвестно")
    name_escaped = escape_markdown(name)

    instructions = {
        "formula": (
            f"➗ Инструкция по формуле {name_escaped}\n\n"
            "1. Открой редактор VBA в Excel (Alt+F11)\n"
            "2. Создай новый модуль: 'Insert' - 'Module'\n"
            "3. Вставь код формулы в открывшемся окне\n"
            "*Код из телеграма копируй с русской раскладкой*\n"
            f"4. Используй в ячейках как ={name_escaped}(...)\n"
            "5. Не забудь сохранить файл в формате *.xlsm*"
        ),
        "macro": (
            f"⚙️ Инструкция по макросу {name_escaped}\n\n"
            "1. Открой редактор VBA в Excel (Alt+F11)\n"
            "2. Создай новый модуль: 'Insert' - 'Module'\n"
            "3. Вставь код макроса в открывшемся окне\n"
            "*Код из телеграма копируй с русской раскладкой*\n"
            "4. Запусти макрос (F5)\n"
            "5. Не забудь сохранить файл в формате *.xlsm*"
        )
    }

    user_id = update.effective_user.id
    user_role = await get_user_role(user_id)
    return await query.message.reply_text(
        text=instructions[instruction_type],
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_role)
    )


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def handle_instruction_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает отказ пользователя от показа инструкции после выбора макроса или формулы.

    Сохраняет пользователя в базе (на случай новых) и возвращает главное меню
    в виде нового сообщения с соответствующей клавиатурой.

    Args:
        update (Update): Объект обновления от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        Message: Сообщение с главным меню.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username

    # 🔄 Сохраняем/обновляем пользователя
    await save_user(user_id, username)
    user_role = await get_user_role(user_id)

    # 🔙 Возвращаем главное меню
    return await update.callback_query.message.reply_text(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard(user_role)
    )


@log_step(question_point=Point.MAIN_MENU, answer_text_getter=lambda msg: msg.text)
async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает нажатие кнопки "⬅️ В главное меню".

    Сохраняет пользователя в базу, очищает `user_data` и заменяет текущее сообщение на главное меню.

    Args:
        update (Update): Объект обновления от Telegram (ожидается CallbackQuery).
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        Message: Сообщение с главным меню.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    username = update.effective_user.username

    # 🔄 Сохраняем/обновляем пользователя
    await save_user(user_id, username)
    user_role = await get_user_role(user_id)

    # 🧹 Очищаем временные данные пользователя
    context.user_data.clear()

    # 🏠 Отправляем главное меню
    return await query.message.edit_text(
        text="🏠 Главное меню:",
        reply_markup=get_main_menu_keyboard(user_role)
    )


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def handle_filter_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает выбор роли из списка доступных (в админ-панели).

    Загружает пользователей по выбранной роли и выводит до 5 пользователей в виде кнопок.
    Если пользователей больше 5, добавляется кнопка "Показать ещё".

    Args:
        update (Update): Объект обновления от Telegram (CallbackQuery с filter_role_).
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram с данными пользователя.

    Returns:
        Message: Обновлённое сообщение со списком пользователей или уведомлением об отсутствии.
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("filter_role_"):
        return

    # 📥 Извлечение выбранной роли
    selected_role = data.replace("filter_role_", "")
    users = await fetch_users_by_role(selected_role)

    # 🔘 Формируем список кнопок
    buttons = []

    if not users:
        text = f"❌ Нет пользователей с ролью `{selected_role}`."
    else:
        text = f"Пользователи с ролью `{selected_role}`:"
        shown_users = users[:5]
        for tg_id, username, phone in shown_users:
            btn_text = f"@{username or 'без username'} | {phone}"
            callback_data = f"user_select_{selected_role}_{tg_id}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

        # 🔄 Добавляем кнопку "Показать ещё", если есть ещё пользователи
        if len(users) > 5:
            buttons.append([
                InlineKeyboardButton("📥 Показать ещё", callback_data=f"show_more_{selected_role}_5")
            ])

    # ⬅️ Кнопка "Назад"
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_roles")])

    return await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def handle_show_more_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает кнопку "Показать ещё" при просмотре пользователей выбранной роли.

    Загружает следующую порцию пользователей (по 5 штук) с указанным смещением.
    Добавляет кнопку для подгрузки ещё и кнопку "Назад".

    Args:
        update (Update): Объект обновления от Telegram (CallbackQuery).
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.

    Returns:
        Message: Обновлённое сообщение с дополнительными пользователями.
    """
    query = update.callback_query
    await query.answer()

    try:
        # 🔹 Извлечение роли и смещения
        parts = query.data.split("_")
        if len(parts) < 4:
            raise ValueError(f"Некорректный формат callback_data: {query.data}")

        role = parts[2]
        offset = int(parts[-1])

    except Exception as e:
        return await query.edit_message_text(f"❌ Неверный формат данных: {e}")

    # 📦 Получение следующей порции пользователей
    users = await get_users_by_role(role, limit=5, offset=offset)
    if not users:
        return await query.edit_message_text(
            f"📭 Больше нет пользователей с ролью `{role}`.",
            parse_mode=ParseMode.MARKDOWN
        )

    # 🔘 Генерация кнопок для новых пользователей
    buttons = []
    for tg_id, username, phone in users:
        btn_text = f"@{username or 'без username'} | {phone}"
        callback_data = f"user_select_{role}_{tg_id}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

    # ➕ Кнопка "Показать ещё", если есть ещё пользователи
    next_offset = offset + 5
    more_users = await get_users_by_role(role, limit=1, offset=next_offset)
    if more_users:
        buttons.append([
            InlineKeyboardButton("📥 Показать ещё", callback_data=f"show_more_{role}_{next_offset}")
        ])

    # ⬅️ Кнопка "Назад"
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_roles")])

    text = f"Пользователи с ролью `{role}` (с {offset + 1}):"
    return await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text)
async def handle_macro_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор макроса из списка.

    Сохраняет имя выбранного макроса в user_data, определяет необходимость шага "выбор столбца",
    и запускает сценарий макроса через соответствующий модуль.

    Args:
        update (Update): Объект обновления от Telegram (CallbackQuery).
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.

    Returns:
        Message: Сообщение с началом сценария выбранного макроса.
    """
    query = update.callback_query
    macro_name = query.data.split(":", 1)[1]

    # 🧠 Сохраняем макрос и возможный начальный шаг
    context.user_data.update({
        "instruction_type": "macro",
        "current_macro_name": macro_name,
        "macro_step": "ask_column" if macro_name in [
            "Преобразовать_столбец_в_число",
            "Фильтр_Строки"
        ] else None
    })

    # ▶️ Запуск сценария макроса
    return await run_macro_scenario(update, context)


@log_step(question_point=Point.ERROR, answer_text_getter=lambda msg: msg.text)
async def handle_formula_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает выбор формулы из списка.

    Извлекает данные по выбранной формуле из БД и отображает код формулы
    с комментарием (если есть), в формате Markdown. Также предлагает инструкцию.

    Args:
        update (Update): Объект обновления Telegram (CallbackQuery).
        context (ContextTypes.DEFAULT_TYPE): Контекст Telegram.

    Returns:
        Message: Сообщение с кодом формулы и предложением инструкции.
    """
    query = update.callback_query
    formula_name = query.data.split(":", 1)[1]
    formula_data = await fetch_formula_by_name(formula_name)

    if not formula_data:
        return await query.message.reply_text("🔍 Формула не найдена")

    _, name, code, comment = formula_data

    response_text = f"*{name}*\n\n```vb\n{code}\n```"

    if comment:
        formatted_comment = format_comment_bold_before_dash(comment)
        response_text += f"\n\n📝 *Комментарий:*\n{formatted_comment}"

    msg = await query.message.reply_text(
        text=response_text,
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data.update({
        "instruction_type": "formula",
        "current_formula_name": name
    })

    await show_instruction_options(update, context)
    return msg


@log_step(question_point=Point.JOKE, answer_text_getter=lambda _: "🎭 Шутка дня: Тук тук")
async def handle_joke_of_the_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет пользователю шутку дня.

    Устанавливает флаг ожидания шутки и логирует ответ бота.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о пользователе и его запросе.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя и его состояние.

    Returns:
        None: Функция ничего не возвращает, но отправляет сообщение с шуткой дня и логирует это событие.
    """
    context.user_data["joke_waiting"] = True

    await reply_with_log(
        update,
        context,
        "🎭 Шутка дня:\nТук тук",
        point=Point.JOKE
    )
