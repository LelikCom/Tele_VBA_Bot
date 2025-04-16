"""
role_monitor.py

Фоновый мониторинг ролей пользователей. При изменении ролей:
- Обновляет команды Telegram
- Очищает сообщения бота у отклонённых пользователей
"""

import asyncio
import functools
import logging
from telegram import BotCommand, BotCommandScopeChat

from db.users import get_all_user_roles
from db.logs import get_bot_messages_for_user, delete_bot_messages_for_user

# Кэши
roles_cache = {}
menu_messages = {}
user_messages = {}


async def role_monitor(bot):
    """
    Запускает бесконечный цикл мониторинга ролей.
    При смене роли на 'rejected' удаляет команды и сообщения.

    Args:
        bot: Экземпляр Telegram-бота.
    """
    logging.info("🎯 Запущен мониторинг ролей пользователей...")

    roles_and_commands = {
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
            users = get_all_user_roles()

            for user_id, role in users:
                prev_role = roles_cache.get(user_id)

                if role != prev_role:
                    roles_cache[user_id] = role
                    scope = BotCommandScopeChat(user_id)
                    commands = roles_and_commands.get(role, [BotCommand("start", "Запустить бота")])

                    try:
                        await bot.set_my_commands(commands=commands, scope=scope)
                    except Exception as e:
                        logging.warning(f"[MONITOR] Не удалось установить команды для {user_id}: {e}")
                        continue

                    if role == "rejected":
                        # 🧹 Удаление inline-меню (если есть)
                        msg_id = menu_messages.pop(user_id, None)
                        if msg_id:
                            try:
                                await bot.delete_message(chat_id=user_id, message_id=msg_id)
                            except Exception as e:
                                logging.warning(f"[MONITOR] Ошибка удаления inline-меню {msg_id} для {user_id}: {e}")

                        # 🧹 Удаление всех сообщений от бота (из dialog_log + Telegram)
                        try:
                            loop = asyncio.get_running_loop()
                            get_msgs = functools.partial(get_bot_messages_for_user, user_id)
                            bot_messages = await loop.run_in_executor(None, get_msgs)

                            for msg_id in bot_messages:
                                try:
                                    await bot.delete_message(chat_id=user_id, message_id=msg_id)
                                except Exception as e:
                                    logging.warning(
                                        f"[MONITOR] Не удалось удалить сообщение {msg_id} для {user_id}: {e}")
                        except Exception as e:
                            logging.error(f"[MONITOR] Ошибка при получении сообщений бота из БД: {e}")

                        # 🧹 Удаление записей из dialog_log
                        try:
                            delete_bot_messages_for_user(user_id)
                            logging.info(f"[MONITOR] Удалены сообщения бота из БД для {user_id}")
                        except Exception as e:
                            logging.error(f"[MONITOR] Ошибка удаления из БД сообщений бота: {e}")

                        # 🧼 Очистка кэша
                        user_messages.pop(user_id, None)

        except Exception as e:
            logging.critical(f"[MONITOR] Глобальная ошибка: {e}", exc_info=True)

        await asyncio.sleep(10)
