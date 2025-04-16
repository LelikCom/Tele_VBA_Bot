"""
handlers.py

Обработка административных запросов и взаимодействия с пользователями:
- Обработка текстовых сообщений
- Добавление комментариев к пользователям
- Просмотр и фильтрация пользователей по ролям
- Обратная связь с пользователями
- Обработка команд для администраторов
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
import os

from macro.macros_logic import run_macro_scenario
from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step
from db.users import (
    update_comment,
    get_all_roles_from_db,
    get_user_role,
)
from macro.utils import reset_macro_state

ADMIN_USER_ID = int(os.getenv("ADMIN_CHAT_ID"))


@log_step(question_point=Point.TEXT, answer_text_getter=lambda msg: msg.text)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает текстовые сообщения пользователя.

    Если пользователь находится в сценарии макроса — продолжает его.
    Иначе отправляет сообщение об ошибке.

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        Message: Ответное сообщение от бота, уведомляющее о дальнейших действиях или ошибке.
    """
    user_data = context.user_data
    step = user_data.get("macro_step")

    if not step:
        return await update.message.reply_text(
            "Я не понял сообщение. Воспользуйся /start или кнопками."
        )

    return await run_macro_scenario(update, context)


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Команда администратора для добавления комментария к пользователю.

    Формат команды: /add_comment <tg_user_id> <текст комментария>

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения команды, содержащий аргументы команды.

    Returns:
        Message: Ответное сообщение от бота, информирующее об успешном добавлении комментария.
    """
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        return await update.message.reply_text("⛔ У вас нет прав на выполнение этой команды.")

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text(
            "❗ Использование: /add_comment <tg_user_id> <текст комментария>"
        )

    try:
        target_user_id = int(args[0])
    except ValueError:
        return await update.message.reply_text("❗ Первый аргумент должен быть числом (tg_user_id).")

    comment_text = " ".join(args[1:])
    update_comment(user_id=target_user_id, comment=comment_text)

    return await update.message.reply_text(
        f"✅ Комментарий успешно добавлен к user_id={target_user_id}."
    )


async def get_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обработчик команды администратора для отображения всех доступных ролей пользователей.

    Проверяет права пользователя и, если это админ, отправляет список ролей
    для дальнейшей фильтрации пользователей.

    Args:
        update (Update): Объект обновления от Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст с данными пользователя.

    Returns:
        Message: Ответное сообщение с клавиатурой ролей для выбора.
    """
    user_id = update.effective_user.id
    message = update.message or update.callback_query.message

    user_role = get_user_role(user_id)

    if user_role == "rejected":
        return

    if user_id != ADMIN_USER_ID:
        return await message.reply_text("⛔ У вас нет прав на выполнение этой команды.")

    roles = get_all_roles_from_db()
    if not roles:
        return await message.reply_text("⚠️ Нет доступных ролей в базе данных.")

    keyboard = [
        [InlineKeyboardButton(text=role, callback_data=f"filter_role_{role}")]
        for role in roles
    ]

    return await message.reply_text(
        "👥 Выберите роль для фильтрации пользователей:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@log_step(question_point=Point.CONFIRM, answer_text_getter=lambda msg: msg.text)
async def handle_back_to_roles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обрабатывает нажатие кнопки "Назад" при просмотре списка пользователей.

    Загружает все уникальные роли из базы данных и предлагает пользователю
    снова выбрать одну из них для фильтрации.

    Args:
        update (Update): Объект обновления от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с пользовательскими данными.

    Returns:
        Message: Ответ с инлайн-клавиатурой, содержащей список ролей.
    """
    query = update.callback_query
    await query.answer()

    roles = get_all_roles_from_db()
    if not roles:
        return await query.edit_message_text("❌ Роли в базе данных не найдены.")

    keyboard = [
        [InlineKeyboardButton(text=role, callback_data=f"filter_role_{role}")]
        for role in roles
    ]

    return await query.edit_message_text(
        "Выберите роль для фильтрации пользователей:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda c: "Обратная связь выбрана")
async def feedback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запускает сценарий обратной связи с пользователем.

    Очищает возможное состояние макроса, переводит пользователя в состояние
    ввода темы обратной связи и запрашивает краткое описание.

    Args:
        update (Update): Объект обновления от Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст с пользовательскими данными.

    Returns:
        None: Функция ничего не возвращает, но отправляет сообщение с запросом темы обратной связи.
    """
    await update.callback_query.answer()

    reset_macro_state(context)

    context.user_data["state"] = "feedback:theme"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=( 
            "📝 Укажи *тему сообщения* — это краткое описание, о чём будет обратная связь.\n"
            "Например: _«Ошибка в отчёте»_, _«Предложение по улучшению»_, _«Проблема с загрузкой»_."
        ),
        parse_mode="Markdown"
    )
