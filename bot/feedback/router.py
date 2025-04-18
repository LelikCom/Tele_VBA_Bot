"""
router.py

Сценарий обратной связи:
- Ввод темы
- Текст сообщения
- Вложения (фото, документ, аудио, видео)
- Сохранение в БД и возврат к start
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from log_dialog.models_daig import Point
from log_dialog.handlers_diag import log_step
from bot.commands.start import start


@log_step(question_point=Point.SCENARIO, answer_text_getter=lambda msg: msg.text if msg.text else "attachment")
async def feedback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод пользователя в сценарии обратной связи.
    Поддерживает: тему, текст сообщения, вложения (фото, документ, аудио, видео).

    Args:
        update (Update): Объект обновления Telegram, содержащий информацию о сообщении.
        context (ContextTypes.DEFAULT_TYPE): Контекст выполнения, содержащий данные пользователя.

    Returns:
        None: Функция отправляет сообщения в чат и сохраняет данные обратной связи.
    """
    state = context.user_data.get("state")
    logging.info(f"[DEBUG] Состояние обратной связи: {state}")

    if not state or not state.startswith("feedback:"):
        return

    if context.user_data.get("macro_step"):
        logging.info("[DEBUG] Пользователь в макросе, игнорируем обратную связь.")
        return

    if state == "feedback:theme":
        context.user_data["feedback_theme"] = update.message.text
        context.user_data["state"] = "feedback:text"

        await update.message.reply_text(
            "✏️ Опиши ситуацию или предложение. "
            "Можешь прикрепить файл — фото, документ или скриншот."
        )
        return

    elif state == "feedback:text":
        theme = context.user_data.get("feedback_theme")
        user_id = update.effective_user.id
        message = update.message
        message_text = message.text or message.caption or "(пусто)"

        attachment = None
        attachment_type = None

        if message.photo:
            attachment = message.photo[-1].file_id
            attachment_type = "photo"
        elif message.document:
            attachment = message.document.file_id
            attachment_type = "document"
        elif message.video:
            attachment = message.video.file_id
            attachment_type = "video"
        elif message.audio:
            attachment = message.audio.file_id
            attachment_type = "audio"

        try:
            from db.feedback import add_feedback
            await add_feedback(user_id, theme, message_text, attachment, attachment_type)
            await message.reply_text("✅ Спасибо! Сообщение получено.")
            logging.info(f"[DEBUG] Обратная связь сохранена от user_id={user_id}")

        except Exception as e:
            await message.reply_text("❌ Ошибка при сохранении. Попробуйте позже.")
            logging.error(f"[ERROR] Ошибка при сохранении обратной связи: {e}")

        context.user_data.pop("state", None)
        context.user_data.pop("feedback_theme", None)

        await start(update, context)
