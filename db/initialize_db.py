import logging
import json
from pathlib import Path
from db.connection import connect_db
import psycopg2

logging.basicConfig(level=logging.INFO)


# Функция для создания таблиц
def create_tables():
    try:
        logging.info("🚀 Подключаемся к базе данных...")

        # Параметры подключения к базе данных
        conn = psycopg2.connect(
            dbname="AIchetovkin",
            user="AIchetovkin",
            password="Ichetovkin",
            host="postgres_db",  # Имя контейнера с базой данных
            port="5432"
        )

        logging.info("✅ Подключение к базе данных установлено.")

        # Создаем курсор для выполнения запросов
        cur = conn.cursor()

        # Запросы для создания таблиц
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
            CREATE TABLE dialog_log (
                id SERIAL PRIMARY KEY,
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

        # Выполняем все запросы
        for query in queries:
            logging.info(f"⚙️ Выполняем запрос: {query[:30]}...")  # Принт для каждого запроса
            cur.execute(query)

        # Сохраняем изменения
        conn.commit()

        logging.info("✅ Все таблицы успешно созданы или уже существуют.")

        # Закрываем курсор и соединение
        cur.close()
        conn.close()

    except Exception as e:
        logging.error(f"❌ Ошибка при создании таблиц: {e}")


# Функции для загрузки данных из JSON файлов
def load_initial_macros(path: Path) -> None:
    try:
        logging.info(f"Загружаем макросы из {path}...")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        macros = data.get("macros", [])
        with connect_db() as conn:
            with conn.cursor() as cur:
                for macro in macros:
                    # Подготовка запроса без комментариев и параметров
                    query = """
                    INSERT INTO vba_unit (vba_name, vba_code)
                    VALUES (%s, %s)
                    ON CONFLICT (vba_name) DO NOTHING
                    """
                    cur.execute(
                        query, (
                            macro["vba_name"],
                            macro["vba_code"]
                        )
                    )
                conn.commit()
        logging.info(f"✅ Загружено макросов: {len(macros)}")
    except Exception as e:
        logging.error(f"❌ Ошибка при загрузке макросов: {e}")


def load_initial_formules(path: Path) -> None:
    try:
        print(f"Загружаем формулы из {path}...")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        formules = data.get("formule", [])
        with connect_db() as conn:
            with conn.cursor() as cur:
                for fml in formules:
                    cur.execute(
                        """
                        INSERT INTO vba_formule (vba_formule_name, vba_formule_code, comment_vba_formule)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (vba_formule_name) DO NOTHING
                        """,
                        (fml["vba_name"], fml["vba_code"], fml.get("comment", "")),
                    )
                conn.commit()
        print(f"✅ Загружено формул: {len(formules)}")
    except Exception as e:
        print(f"❌ Ошибка при загрузке формул: {e}")


def load_initial_admins(path: Path) -> None:
    try:
        print(f"Загружаем администраторов из {path}...")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        admins = data.get("admins", [])
        with connect_db() as conn:
            with conn.cursor() as cur:
                for admin in admins:
                    cur.execute(
                        """
                        INSERT INTO User_Contacts_VBA (user_id, username, phone_number, comment, role)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE
                        SET username = EXCLUDED.username,
                            phone_number = COALESCE(EXCLUDED.phone_number, User_Contacts_VBA.phone_number),
                            comment = EXCLUDED.comment,
                            role = EXCLUDED.role
                        """,
                        (
                            admin["user_id"],
                            admin.get("username"),
                            admin.get("phone_number"),
                            admin.get("comment", ""),
                            admin.get("role", "admin"),
                        ),
                    )
                conn.commit()
        print(f"✅ Загружено администраторов: {len(admins)}")
    except Exception as e:
        print(f"❌ Ошибка при загрузке администраторов: {e}")


def populate_initial_data() -> None:
    print("Загружаем начальные данные в базу данных...")
    seeds_dir = Path(__file__).parent / "seeds"
    load_initial_macros(seeds_dir / "macros.json")
    load_initial_formules(seeds_dir / "formules.json")
    load_initial_admins(seeds_dir / "admin_users.json")


# Запускаем необходимые функции сразу при запуске скрипта
create_tables()  # Для создания таблиц
populate_initial_data()  # Для загрузки начальных данных