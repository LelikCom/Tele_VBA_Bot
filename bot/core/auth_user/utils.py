import os


def get_available_roles() -> list[str]:
    """
    Возвращает список доступных ролей из переменной окружения `AVAILABLE_ROLES`.

    Returns:
        list[str]: Список ролей.
    """
    roles = os.getenv("AVAILABLE_ROLES", "")
    return [role.strip() for role in roles.split(",") if role.strip()]
