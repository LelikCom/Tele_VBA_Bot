"""
role_monitor.py

Фоновый мониторинг ролей пользователей. При изменении ролей:
- Обновляет команды Telegram
- Очищает сообщения бота у отклонённых пользователей
"""

import asyncio
import logging
from telegram import BotCommand, BotCommandScopeChat

from db.users import get_all_user_roles
from db.logs import get_bot_messages_for_user, delete_bot_messages_for_user

# Кэши
roles_cache: dict[int, str] = {}
menu_messages: dict[int, int] = {}
user_messages: dict[int, list[int]] = {}


async def role_monitor(bot) -> None:
    """
    Запускает бесконечный цикл мониторинга ролей.
    При смене роли на 'rejected' удаляет команды и сообщения.

    Args:
        bot: Экземпляр Telegram-бота.
    """
    logging.info("🎯 Запущен мониторинг ролей пользователей...")

    roles_and_commands: dict[str, list[BotCommand]] = {
        "admin": [
            BotCommand("start", "Запустить бота"),
            BotCommand("get_users", "Получить данные пользователей"),
        ],
        "auth": [BotCommand("start", "Запустить бота")],
        "preauth": [BotCommand("start", "Запустить бота")],
        "noauth": [BotCommand("start", "Запустить бота")],
        "rejected": []
    }

    while True:
        try:
            users = await get_all_user_roles()

            for user_id, role in users:
                prev_role = roles_cache.get(user_id)
                if role == prev_role:
                    continue

                # Обновляем кэш и команды
                roles_cache[user_id] = role
                scope = BotCommandScopeChat(user_id)
                commands = roles_and_commands.get(role, [BotCommand("start", "Запустить бота")])
                try:
                    await bot.set_my_commands(commands=commands, scope=scope)
                except Exception as e:
                    logging.warning(f"[MONITOR] Не удалось установить команды для {user_id}: {e}")

                # Действия для rejected
                if role == "rejected":
                    # Удаление inline-меню
                    msg_id = menu_messages.pop(user_id, None)
                    if msg_id is not None:
                        try:
                            await bot.delete_message(chat_id=user_id, message_id=msg_id)
                        except Exception as e:
                            logging.warning(f"[MONITOR] Ошибка удаления inline-меню {msg_id} для {user_id}: {e}")

                    # Удаление сообщений от бота
                    try:
                        bot_messages = await get_bot_messages_for_user(user_id)
                        for msg_id in bot_messages:
                            try:
                                await bot.delete_message(chat_id=user_id, message_id=msg_id)
                            except Exception as e:
                                logging.warning(f"[MONITOR] Не удалось удалить сообщение {msg_id} для {user_id}: {e}")
                    except Exception as e:
                        logging.error(f"[MONITOR] Ошибка при получении сообщений бота из БД: {e}")

                    # Удаление записей из dialog_log
                    try:
                        await delete_bot_messages_for_user(user_id)
                        logging.info(f"[MONITOR] Удалены сообщения бота из БД для {user_id}")
                    except Exception as e:
                        logging.error(f"[MONITOR] Ошибка удаления из БД сообщений бота: {e}")

                    # Очистка кэша пользовательских сообщений
                    user_messages.pop(user_id, None)

        except Exception:
            logging.critical("[MONITOR] Глобальная ошибка", exc_info=True)

        await asyncio.sleep(10)