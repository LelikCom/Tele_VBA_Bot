from html import escape, unescape
import re
from telegram import Message
from telegram.constants import ParseMode


def safe_format_html(text: str) -> str:
    """
    Безопасное форматирование текста в HTML для Telegram.

    :param text: исходный текст
    :return: безопасный HTML-текст
    """
    if not text:
        return ""

    # Декодируем HTML сущности
    raw = unescape(text)

    # Убираем таблицы Markdown
    raw = re.sub(r'^\|[-\s|]{3,}\|$', '', raw, flags=re.MULTILINE)

    # Извлекаем код-блоки и заменяем их на плейсхолдеры
    code_blocks = []

    def extract_block(match):
        code = match.group(1)
        safe_code = escape(code, quote=False)
        placeholder = f"@@CODE{len(code_blocks)}@@"
        code_blocks.append(f"📄 <b>Код:</b>\n<pre><code>{safe_code}</code></pre>")
        return placeholder

    raw = re.sub(
        r'(?:```|\'\'\')[^\n]*\n(.*?)\n(?:```|\'\'\')',
        extract_block,
        raw,
        flags=re.DOTALL,
    )

    # Экранируем оставшийся текст
    escaped = escape(raw, quote=False)

    # Форматируем заголовки, жирный и курсивный текст
    escaped = re.sub(r'^###\s*(.+)$', lambda m: f'📘 <b>{m.group(1)}</b>', escaped, flags=re.MULTILINE)
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped, flags=re.DOTALL)
    escaped = re.sub(r'\*(.+?)\*', r'<i>\1</i>', escaped, flags=re.DOTALL)
    escaped = re.sub(r'\\boxed\{([^}]+)\}', lambda m: f"<b>Ответ: {m.group(1)}</b>", escaped)

    # Форматируем инлайн-код после других преобразований
    escaped = re.sub(r'(?<!>)`([^`\n]+?)`(?!<)', lambda m: f"<code>{escape(m.group(1), quote=False)}</code>", escaped)

    # Возвращаем код-блоки на место
    for i, block in enumerate(code_blocks):
        escaped = escaped.replace(f"@@CODE{i}@@", block)

    return escaped


async def send_long_message(message: Message, text: str, chunk_size: int = 4096, parse_mode: str = ParseMode.HTML):
    """
    Отправляет длинное сообщение частями в Telegram.

    :param message: объект telegram.Message, на который нужно ответить
    :param text: текст для отправки
    :param chunk_size: максимальная длина одного сообщения
    :param parse_mode: режим форматирования текста (HTML или MarkdownV2)
    """
    if not text:
        return

    safe_chunk_size = chunk_size - 200  # резервируем место под управляющие символы
    chunks = [text[i:i + safe_chunk_size] for i in range(0, len(text), safe_chunk_size)]

    if len(chunks) == 1:
        await message.reply_text(chunks[0], parse_mode=parse_mode)
    else:
        try:
            status_msg = await message.reply_text("⏳ Отправка длинного ответа...")
            await status_msg.edit_text(chunks[0], parse_mode=parse_mode)
        except Exception:
            # если редактирование не удалось, просто отправляем отдельное сообщение
            await message.reply_text(chunks[0], parse_mode=parse_mode)

        # отправляем оставшиеся куски
        for chunk in chunks[1:]:
            await message.reply_text(chunk, parse_mode=parse_mode)
