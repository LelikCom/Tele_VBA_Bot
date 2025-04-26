import os

def is_deepseek_available() -> bool:
    """
    Проверяет, доступен ли DeepSeek API (есть ли API-ключ в окружении).

    Returns:
        bool: True, если API-ключ задан, иначе False.
    """
    return bool(os.getenv("DEEPSEEK_API_KEY"))
