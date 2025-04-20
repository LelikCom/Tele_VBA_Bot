import uuid
import logging
from db.connection import get_db_connection
from datetime import datetime, timedelta
import pytz
from dateutil import parser

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='bot_errors.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

moscow = pytz.timezone("Europe/Moscow")
SESSION_TIMEOUT_MINUTES = 1


async def get_or_create_session(user_id: int) -> tuple[str, int]:
    """
    Проверяет активную сессию пользователя. Возвращает session_id и следующий step.
    Если прошло более SESSION_TIMEOUT_MINUTES — создаёт новую сессию.

    Args:
        user_id (int): ID пользователя.

    Returns:
        tuple[str, int]: session_id и номер следующего шага.
    """
    now_msk = datetime.now(moscow).replace(tzinfo=None)

    # Получаем последнюю сессию из базы данных
    query = """
        SELECT session_id, step, time_question
        FROM dialog_log
        WHERE user_id = $1
        ORDER BY time_question DESC
        LIMIT 1
    """

    try:
        logging.debug(f"[БД] Выполнение запроса для получения последней сессии пользователя {user_id}")
        async with get_db_connection() as conn:
            record = await conn.fetchrow(query, user_id)
            if record:
                session_id, last_step, last_time = record
                if isinstance(last_time, str):
                    last_time = parser.parse(last_time)
                if isinstance(last_time, datetime):
                    last_time = last_time.replace(tzinfo=None)

                if (now_msk - last_time) < timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                    logging.info(f"Для пользователя {user_id} найдена активная сессия.")
                    return session_id, last_step + 1

            # Если сессия не найдена или она устарела — генерируем новую
            session_id = str(uuid.uuid4())  # Генерация нового session_id
            logging.info(f"[БД] Сессия для пользователя {user_id} не найдена или устарела. Сгенерирован новый session_id: {session_id}")
            return session_id, 1  # Возвращаем новый session_id и первый шаг

    except Exception as e:
        logging.error(f"[БД] Ошибка при получении сессии для пользователя {user_id}: {e}")
        # В случае ошибки генерируем новую сессию
        session_id = str(uuid.uuid4())
        logging.info(f"[БД] Произошла ошибка при получении сессии. Сгенерирован новый session_id: {session_id}")
        return session_id, 1  # Возвращаем новый session_id и первый шаг


async def insert_question(
        user_id: int,
        username: str,
        message_id: int,
        message_text: str,
        point: str
) -> None:
    """
    Сохраняет сообщение пользователя в таблицу dialog_log.
    Включает логику создания сессии и шага.

    Args:
        user_id (int): Telegram ID пользователя.
        username (str): Username пользователя.
        message_id (int): ID сообщения.
        message_text (str): Текст вопроса.
        point (str): Точка сценария (например, "CONTACT").
    """
    session_id, step = await get_or_create_session(user_id)  # Получаем или создаем сессию и шаг
    now_msk = datetime.now(moscow).replace(tzinfo=None)

    query = """
        INSERT INTO dialog_log (
            session_id, step, user_id, username,
            id_question, question, time_question, point
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """

    # Логируем сам SQL запрос
    logging.debug(f"[БД] SQL запрос: {query}, параметры: session_id={session_id}, step={step}, "
                  f"user_id={user_id}, username={username}, message_id={message_id}, "
                  f"question={message_text}, point={point}, time_question={now_msk}")

    try:
        async with get_db_connection() as conn:
            await conn.execute(
                query,
                session_id, step, user_id, username,
                message_id, message_text, now_msk, point
            )
        logging.info(f"[БД] Вопрос для пользователя {user_id} успешно сохранён в базу данных. Текст: '{message_text}'")
    except Exception as e:
        logging.error(f"[БД] Ошибка при сохранении вопроса для user_id={user_id}: {e}")


async def insert_answer(
        user_id: int,
        message_id: int,
        answer_text: str
) -> None:
    """
    Обновляет последний вопрос пользователя в dialog_log, добавляя ответ.
    Включает логику создания сессии и шага.

    Args:
        user_id (int): Telegram ID пользователя.
        message_id (int): ID ответа бота.
        answer_text (str): Текст ответа.
    """
    session_id, step = await get_or_create_session(user_id)
    now_msk = datetime.now(moscow).replace(tzinfo=None)

    query = """
        UPDATE dialog_log
        SET id_answer = $1, answer = $2, time_answer = $3
        WHERE user_id = $4 AND id_answer IS NULL
        AND step = (
            SELECT MAX(step)
            FROM dialog_log
            WHERE user_id = $4 AND id_answer IS NULL
        )
    """

    # Логируем сам SQL запрос
    logging.debug(f"[БД] SQL запрос: {query}, параметры: message_id={message_id}, answer={answer_text}, "
                  f"time_answer={now_msk}, user_id={user_id}")

    try:
        async with get_db_connection() as conn:
            await conn.execute(
                query,
                message_id, answer_text, now_msk, user_id
            )
    except Exception as e:
        logging.error(f"[БД] Ошибка при сохранении ответа для user_id={user_id}: {e}")