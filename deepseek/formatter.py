from html import escape, unescape
import re
from telegram import Message
from telegram.constants import ParseMode


def safe_format_html(text: str) -> str:
    """
    Безопасное форматирование текста в HTML для Telegram.

    Args:
        text (str): Исходный текст для форматирования.

    Returns:
        str: Безопасно отформатированный HTML-текст, готовый для отправки в Telegram.

    Примечания:
        - Экранирует специальные символы.
        - Преобразует Markdown-разметку в HTML.
        - Переводит код-блоки в формат Telegram.
    """
    if not text:
        return ""

    raw = unescape(text)

    raw = re.sub(r"^\|[-\s|]{3,}\|$", "", raw, flags=re.MULTILINE)

    code_blocks = []

    def extract_block(match):
        code = match.group(1)
        safe_code = escape(code, quote=False)
        placeholder = f"@@CODE{len(code_blocks)}@@"
        code_blocks.append(f"📄 <b>Код:</b>\n<pre><code>{safe_code}</code></pre>")
        return placeholder

    raw = re.sub(
        r"(?:```|''')[^\n]*\n(.*?)\n(?:```|''')",
        extract_block,
        raw,
        flags=re.DOTALL,
    )

    escaped = escape(raw, quote=False)

    escaped = re.sub(
        r"^###\s*(.+)$",
        lambda m: f"📘 <b>{m.group(1)}</b>",
        escaped,
        flags=re.MULTILINE,
    )
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped, flags=re.DOTALL)
    escaped = re.sub(r"\*(.+?)\*", r"<i>\1</i>", escaped, flags=re.DOTALL)
    escaped = re.sub(
        r"\\boxed\{([^}]+)\}",
        lambda m: f"<b>Ответ: {m.group(1)}</b>",
        escaped,
    )

    escaped = re.sub(
        r"(?<!>)`([^`\n]+?)`(?!<)",
        lambda m: f"<code>{escape(m.group(1), quote=False)}</code>",
        escaped,
    )

    for i, block in enumerate(code_blocks):
        escaped = escaped.replace(f"@@CODE{i}@@", block)

    return escaped


async def send_long_message(
    message: Message,
    text: str,
    chunk_size: int = 4096,
    parse_mode: str = ParseMode.HTML,
):
    """
    Отправляет длинное сообщение частями в Telegram.

    Args:
        message (Message): Объект сообщения Telegram, на который нужно ответить.
        text (str): Текст для отправки.
        chunk_size (int, optional): Максимальный размер одного сообщения. По умолчанию 4096.
        parse_mode (str, optional): Режим форматирования текста (HTML или MarkdownV2). По умолчанию HTML.

    Side Effects:
        Отправляет одно или несколько сообщений в чат Telegram.
    """
    if not text:
        return

    safe_chunk_size = chunk_size - 200
    chunks = [
        text[i : i + safe_chunk_size] for i in range(0, len(text), safe_chunk_size)
    ]

    if len(chunks) == 1:
        await message.reply_text(chunks[0], parse_mode=parse_mode)
    else:
        try:
            status_msg = await message.reply_text("⏳ Отправка длинного ответа...")
            await status_msg.edit_text(chunks[0], parse_mode=parse_mode)
        except Exception:
            await message.reply_text(chunks[0], parse_mode=parse_mode)

        for chunk in chunks[1:]:
            await message.reply_text(chunk, parse_mode=parse_mode)
