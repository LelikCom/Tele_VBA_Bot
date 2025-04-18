import logging
import json
import asyncio
from pathlib import Path
from db.connection import init_db_pool, close_db_pool, get_db_connection

logging.basicConfig(level=logging.INFO)


async def create_tables() -> None:
    """
    Создаёт таблицы в базе данных, если они не существуют.
    """
    queries = [
        """
        CREATE TABLE IF NOT EXISTS User_Contacts_VBA (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            phone_number TEXT,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL
                      DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Moscow'),
            comment TEXT,
            role TEXT NOT NULL DEFAULT 'noauth'
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS vba_unit (
            id SERIAL PRIMARY KEY,
            vba_name TEXT NOT NULL UNIQUE,
            vba_code TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS vba_formule (
            id SERIAL PRIMARY KEY,
            vba_formule_name TEXT NOT NULL UNIQUE,
            vba_formule_code TEXT NOT NULL,
            comment_vba_formule TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            theme TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            attachment TEXT,
            attachment_type TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
                        DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Moscow')
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dialog_log (
            session_id TEXT NOT NULL,
            step INT NOT NULL,
            user_id BIGINT NOT NULL,
            username TEXT NOT NULL,
            id_question INT NOT NULL,
            question TEXT NOT NULL,
            time_question TIMESTAMP NOT NULL,
            id_answer INT,
            answer TEXT,
            time_answer TIMESTAMP,
            point TEXT
        );
        """
    ]
    async with get_db_connection() as conn:
        for sql in queries:
            await conn.execute(sql)


async def load_initial_macros(path: Path) -> None:
    """
    Загружает макросы из JSON в таблицу vba_unit.

    Args:
        path (Path): Путь до JSON-файла с макросами.
    """
    logging.info(f"Загружаем макросы из {path}...")
    data = json.loads(path.read_text(encoding="utf-8"))
    macros = data.get("macros", [])
    async with get_db_connection() as conn:
        for macro in macros:
            sql = """
            INSERT INTO vba_unit (vba_name, vba_code)
            VALUES ($1, $2)
            ON CONFLICT (vba_name) DO NOTHING
            """
            await conn.execute(sql, macro["vba_name"], macro["vba_code"])
    logging.info(f"✅ Загружено макросов: {len(macros)}")


async def load_initial_formules(path: Path) -> None:
    """
    Загружает формулы из JSON в таблицу vba_formule.

    Args:
        path (Path): Путь до JSON-файла с формулами.
    """
    logging.info(f"Загружаем формулы из {path}...")
    data = json.loads(path.read_text(encoding="utf-8"))
    formules = data.get("formule", [])
    async with get_db_connection() as conn:
        for fml in formules:
            sql = """
            INSERT INTO vba_formule (vba_formule_name, vba_formule_code, comment_vba_formule)
            VALUES ($1, $2, $3)
            ON CONFLICT (vba_formule_name) DO NOTHING
            """
            await conn.execute(sql, fml["vba_name"], fml["vba_code"], fml.get("comment", ""))
    logging.info(f"✅ Загружено формул: {len(formules)}")


async def load_initial_admins(path: Path) -> None:
    """
    Загружает администраторов из JSON в таблицу User_Contacts_VBA.

    Args:
        path (Path): Путь до JSON-файла с данными администраторов.
    """
    logging.info(f"Загружаем администраторов из {path}...")
    data = json.loads(path.read_text(encoding="utf-8"))
    admins = data.get("admins", [])
    async with get_db_connection() as conn:
        for admin in admins:
            sql = """
            INSERT INTO User_Contacts_VBA (user_id, username, phone_number, timestamp, comment, role)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Moscow', $4, $5)
            ON CONFLICT (user_id) DO UPDATE
            SET username = EXCLUDED.username,
                phone_number = COALESCE(EXCLUDED.phone_number, User_Contacts_VBA.phone_number),
                comment = EXCLUDED.comment,
                role = EXCLUDED.role
            """
            await conn.execute(
                sql,
                admin["user_id"],
                admin.get("username"),
                admin.get("phone_number"),
                admin.get("comment", ""),
                admin.get("role", "admin"),
            )
    logging.info(f"✅ Загружено администраторов: {len(admins)}")


async def populate_initial_data() -> None:
    """
    Запускает загрузку всех начальных данных из директории seeds.
    """
    seeds_dir = Path(__file__).parent / "seeds"
    await load_initial_macros(seeds_dir / "macros.json")
    await load_initial_formules(seeds_dir / "formules.json")
    await load_initial_admins(seeds_dir / "admin_users.json")


async def main() -> None:
    """
    Основная точка входа: инициализация пула, создание таблиц и наполнение данными.
    """
    await init_db_pool()
    await create_tables()
    await populate_initial_data()
    await close_db_pool()


if __name__ == "__main__":
    asyncio.run(main())
