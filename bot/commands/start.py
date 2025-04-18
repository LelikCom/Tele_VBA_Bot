"""
start.py

Обработчик команды /start.
Приветствует пользователя в зависимости от его роли.
"""

import logging
from telegram import Update, Message
from telegram.ext import ContextTypes

from bot.core.keyboards.main_menu import get_main_menu_keyboard
from db.users import save_user, get_user_role
from macro.utils import send_response
from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step


@log_step(question_point=Point.MAIN_MENU, answer_text_getter=lambda msg: msg.text)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Обработчик команды /start. Показывает главное меню в зависимости от роли пользователя.

    Args:
        update (Update): Объект Telegram обновления.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения.

    Returns:
        Message: Отправленное сообщение Telegram.
    """
    user = update.effective_user
    await save_user(user.id, user.username)
    user_role = await get_user_role(user.id)

    logging.info(f"[START] user_id={user.id} | username={user.username} | role={user_role}")

    match user_role:
        case "noauth":
            welcome_text = (
                "Привет! Я бот, который умеет:\n"
                "1) Строить формулы\n"
                "2) Писать макросы\n\n"
                "Для доступа ко всему функционалу тебе нужно пройти авторизацию🔐"
            )
        case "auth":
            welcome_text = (
                "Привет! Я бот, который умеет:\n"
                "1) Строить формулы\n"
                "2) Писать макросы\n"
                "3) Делать SQL-запросы\n"
                "4) И рассказывать шутки!\n\n"
                "Выбирай, чем займемся 📚"
            )
        case "admin":
            welcome_text = (
                "С возвращением, админ!\n"
                "Ты можешь:\n"
                "1) Управлять формулами и макросами\n"
                "2) Делать SQL-запросы\n"
                "3) Читать обратную связь\n"
                "4) Администрировать пользователей\n\n"
                "Что делаем?"
            )
        case "preauth":
            welcome_text = (
                "Ты почти внутри!\n"
                "Пока доступны только базовые функции:\n"
                "1) Формулы\n"
                "2) Макросы\n\n"
                "Ожидай подтверждения доступа🕓"
            )
        case _:
            welcome_text = (
                "Привет! Тебя заблокировали.\n"
                "Для разблокировки обратись: https://t.me/AIchetovkin"
            )

    return await send_response(update, welcome_text, keyboard=get_main_menu_keyboard(user_role))
