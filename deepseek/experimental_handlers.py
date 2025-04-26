from telegram import Update, constants
from telegram.ext import ContextTypes
import json
import logging
from pathlib import Path

from deepseek.experimental import WARNING_TEXT, back_keyboard
from db.users import get_user_role_by_id

# Загрузка разрешённых действий один раз при старте
allowed_actions_path = Path('bot/core/auth_user/allowed_actions.json')
with allowed_actions_path.open('r', encoding='utf-8') as f:
    allowed_actions = json.load(f)


async def experimental_ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет предупреждение об экспериментальной функции и кнопку «Назад».

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Side Effects:
        Отправляет сообщение с текстом предупреждения и встроенной клавиатурой.
    """
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id
    user_role = await get_user_role_by_id(user_id)
    allowed_roles = allowed_actions.get('experimental_ai', [])

    if user_role in allowed_roles:
        await q.message.reply_text(
            WARNING_TEXT,
            reply_markup=back_keyboard(),
            parse_mode=constants.ParseMode.HTML,
        )
    else:
        await q.message.reply_text(
            "У вас нет доступа к этой функции.",
            parse_mode=constants.ParseMode.HTML,
        )


async def back_to_prev_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает возврат к предыдущему состоянию, удаляя сообщение.

    Args:
        update (Update): Объект обновления Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст текущего взаимодействия.

    Side Effects:
        Удаляет сообщение, содержащее предупреждение или другой текст.
    """
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id
    user_role = await get_user_role_by_id(user_id)
    allowed_roles = allowed_actions.get('back_to_prev', [])

    if user_role in allowed_roles:
        try:
            await q.message.delete()
        except Exception as e:
            logging.error(f"Ошибка при удалении сообщения: {e}")
    else:
        await q.message.reply_text(
            "У вас нет прав для выполнения этого действия.",
            parse_mode=constants.ParseMode.HTML,
        )
