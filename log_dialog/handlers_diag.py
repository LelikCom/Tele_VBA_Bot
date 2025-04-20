import functools
import logging
from telegram import Update, Message
from telegram.ext import ContextTypes

from log_dialog.models_daig import Point
from db.users import get_user_role_by_id
from db.dialog_log import insert_question, insert_answer
from db.users import get_user_role

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='bot_errors.log',
    level=logging.DEBUG,
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
    logging.info(f"Ошибка для пользователя {user_id}: {error}")


def log_step(question_point: str = Point.MAIN_MENU, answer_text_getter=lambda msg: getattr(msg, 'text', '')):
    """
    Декоратор для логирования шагов пользователя.

    Логирование происходит только если роль пользователя не 'rejected' или 'admin'.

    Args:
        question_point (str): Точка сценария для логирования.
        answer_text_getter (callable): Функция для получения текста ответа.

    Returns:
        decorator: Возвращает декоратор, который применяет логирование к функции.
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

                user_role = await get_user_role_by_id(user_id)

                if user_role in ['rejected', 'admin']:
                    return await func(update, context, *args, **kwargs)

                # Логируем вопрос
                await insert_question(
                    user_id=user_id,
                    username=username,
                    message_id=message.message_id if message else 'N/A',
                    message_text=text,
                    point=question_point
                )

                result = await func(update, context, *args, **kwargs)

                if isinstance(result, Message):
                    answer_text = answer_text_getter(result) or "Ответ без текста"
                    await insert_answer(
                        user_id=user_id,
                        message_id=result.message_id,
                        answer_text=answer_text
                    )
                return result

            except Exception as e:
                logging.error(f"Ошибка при логировании шага: {e}")
                return await func(update, context, *args, **kwargs)

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
        logging.warning("Не удалось получить пользователя для логирования вопроса.")
        return

    role = await get_user_role_by_id(user.id)
    logging.debug(f"Получена роль пользователя {user.id}: {role}")

    if role not in ("auth", "noauth", "preauth"):
        logging.info(f"Пользователь {user.id} с ролью {role} не попадает под логи вопросов.")
        return

    message = update.message or (update.callback_query.message if update.callback_query else None)
    text = update.message.text if update.message else (
        update.callback_query.data if update.callback_query else ''
    )

    if message and text:
        logging.debug(f"Получен вопрос от пользователя {user.id}: {text}")

        logging.info(f"Вопрос от пользователя {user.id}: {text}")

        logging.debug(f"Данные для логирования вопроса: session_id={update.effective_chat.id}, "
                      f"step={point}, user_id={user.id}, username={user.username}, "
                      f"message_id={message.message_id}, question={text}, point={point}")

        await insert_question(
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
        logging.error(f"[Handler] Ошибка: отсутствует пользователь или сообщение.")
        return

    try:
        role = await get_user_role_by_id(user.id)
        logging.debug(f"[Handler] Роль пользователя {user.id}: {role}")
    except Exception as e:
        logging.error(f"[Handler] Ошибка при получении роли для пользователя {user.id}: {e}")
        return

    if role not in ("auth", "noauth", "preauth"):
        logging.debug(f"[Handler] Роль {role} не подходит для логирования.")
        return

    try:
        logging.debug(
            f"[Handler] Логируем сообщение для пользователя {user.id}, message_id: {msg_obj.message_id}, answer_text: {answer_text}")
        await insert_answer(
            user_id=user.id,
            message_id=msg_obj.message_id,
            answer_text=answer_text
        )
        logging.info(f"[Handler] Ответ успешно сохранён в базе данных для пользователя {user.id}.")
    except Exception as e:
        logging.error(f"[Handler] Ошибка при логировании ответа для пользователя {user.id}: {e}")
        logging.debug(f"[Handler] Текст ошибки: {e}")
        logging.error(f"[Handler] Не удалось записать ответ в базу данных.")

    return





