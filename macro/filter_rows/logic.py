"""
logic.py

Модуль генерации макросов для фильтрации строк в Excel.
Подставляет пользовательские данные в шаблон и возвращает экранированный макрос.
"""

import logging
from telegram.helpers import escape_markdown


from telegram.helpers import escape_markdown
import logging


def build_macro_from_context(macro_template: str, context_data: dict) -> str:
    """
    Генерирует финальный текст макроса, подставляя параметры из context.user_data в шаблон.

    Args:
        macro_template (str): Шаблон макроса с плейсхолдерами.
        context_data (dict): Данные пользователя из context.user_data.

    Returns:
        str: Готовый макрос с подставленными значениями, экранированный для MarkdownV2.
    """
    mode = context_data.get("mode")
    if not mode:
        raise ValueError("Не указан режим фильтрации (manual/range)")

    try:
        params = {
            "{user_input_column}": str(context_data["column_num"]),
            "{user_input_mode}": mode
        }

        if mode == "manual":
            values = context_data.get("values", [])
            raw_values = ", ".join(f'"{v}"' for v in values)
            params["{user_input_values}"] = raw_values
        else:
            range_raw = context_data["selected_range"]
            params.update({
                "{user_input_sheet}": context_data["sheet"],
                "{user_input_range}": range_raw.split("!", 1)[-1] if "!" in range_raw else range_raw,
                "{user_input_values}": '""'
            })

        for placeholder, value in params.items():
            macro_template = macro_template.replace(placeholder, value)

        escaped_parts = []
        for line in macro_template.splitlines():
            if "Array(" in line:
                escaped_parts.append(line)
            else:
                escaped_parts.append(escape_markdown(line, version=2))
        return "\n".join(escaped_parts)

    except KeyError as e:
        logging.error(f"Отсутствует обязательный параметр: {e}")
        raise
    except Exception as e:
        logging.error(f"Ошибка при генерации макроса: {e}")
        raise

