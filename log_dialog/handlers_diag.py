"""
handlers_diag.py

Логирование вопросов и ответов пользователей:
- Логирование вопросов пользователей (для ролей "auth", "noauth", "preauth").
- Логирование ответов бота.
- Обработка ошибок и хранение логов в файле `bot_errors.log`.
"""

import functools
import logging
from telegram import Update, Message
from telegram.ext import ContextTypes

from log_dialog.logger import log_question, log_answer
from log_dialog.models_daig import Point
from db.users import get_user_role_by_id

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='bot_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def log_error(user_id: str, error: str):
    """
    Логирует ошибку с ID пользователя.

    Args:
        user_id (str): ID пользователя, для которого произошла ошибка.
        error (str): Описание ошибки.
    """
    logger.error(f"Ошибка у пользователя {user_id}: {error}")


def log_step(question_point: str = Point.TEXT, answer_text_getter=lambda msg: getattr(msg, 'text', '')):
    """
    Декоратор для логирования вопросов и ответов в процессе выполнения функции.

    Логирует входящее сообщение пользователя, выполняет основную функцию и логирует её ответ.

    Args:
        question_point (str): Точка сценария, для которой будет зафиксирован вопрос.
        answer_text_getter (callable): Функция для извлечения текста ответа из объекта Message.

    Returns:
        wrapper (function): Обёртка для логирования и выполнения основной функции.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = None
            try:
                message = (
                    update.message
                    or update.edited_message
                    or (update.callback_query.message if update.callback_query else None)
                )
                text = (
                    (update.message.text if update.message else '')
                    or (update.callback_query.data if update.callback_query else '')
                )

                user_id = update.effective_user.id if update.effective_user else "unknown"
                username = update.effective_user.username if update.effective_user else "unknown"

                role = await get_user_role_by_id(user_id)
                should_log = role in ("auth", "noauth", "preauth")

                if message and text and should_log:
                    await log_question(
                        user_id=user_id,
                        username=username,
                        message_id=message.message_id,
                        message_text=text,
                        point=question_point
                    )

                result = await func(update, context, *args, **kwargs)

                if isinstance(result, Message) and should_log:
                    answer_text = answer_text_getter(result) or "Ответ без текста"
                    await log_answer(
                        user_id=user_id,
                        message_id=result.message_id,
                        answer_text=answer_text
                    )

                return result

            except Exception as e:
                raise

        return wrapper
    return decorator


async def log_user_question(update: Update, context: ContextTypes.DEFAULT_TYPE, point: str = Point.TEXT):
    """
    Логирует входящее сообщение пользователя как вопрос (только если его роль — auth или noauth).

    Функция сохраняет вопрос пользователя в лог, если его роль соответствует одной из разрешённых (auth, noauth, preauth).

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.
        point (str): Точка сценария для логирования (по умолчанию Point.TEXT).

    Returns:
        None: Функция ничего не возвращает, но выполняет логирование вопроса.
    """
    user = update.effective_user
    if not user:
        return

    role = await get_user_role_by_id(user.id)
    if role not in ("auth", "noauth", "preauth"):
        return

    message = update.message or (update.callback_query.message if update.callback_query else None)
    text = update.message.text if update.message else (
        update.callback_query.data if update.callback_query else ''
    )

    if message and text:
        await log_question(
            user_id=user.id,
            username=user.username,
            message_id=message.message_id,
            message_text=text,
            point=point
        )


async def log_bot_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, msg_obj: Message, answer_text: str):
    """
    Логирует ответ бота (msg_obj — это объект Message, возвращённый send/reply), только для auth и noauth.

    Функция сохраняет ответ бота в лог, если роль пользователя соответствует одной из разрешённых (auth, noauth, preauth).

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.
        msg_obj (Message): Объект сообщения от бота, который нужно залогировать.
        answer_text (str): Текст ответа бота для логирования.

    Returns:
        None: Функция ничего не возвращает, но выполняет логирование ответа.
    """
    user = update.effective_user if isinstance(update, Update) else update.from_user
    if not user or not msg_obj:
        logging.error(f"Ошибка логирования: не удалось получить пользователя или сообщение.")
        return

    role = await get_user_role_by_id(user.id)
    if role not in ("auth", "noauth", "preauth"):
        logging.warning(f"Роль пользователя {user.id} не позволяет логировать сообщение.")
        return

    try:
        await log_answer(
            user_id=user.id,
            message_id=msg_obj.message_id,
            answer_text=answer_text
        )
        logging.info(f"log_bot_answer: logged answer for user {user.id}, message_id {msg_obj.message_id}")
    except Exception as e:
        logging.error(f"log_bot_answer: failed to log bot answer: {e}")
