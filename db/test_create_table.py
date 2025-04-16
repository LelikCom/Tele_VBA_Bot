import psycopg2
import logging

# Настроим логирование
logging.basicConfig(level=logging.INFO)


def create_test_table():
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

        # Запрос для создания тестовой таблицы
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        );
        """
        logging.info("⚙️ Выполняем запрос для создания таблицы...")
        cur.execute(create_table_query)

        # Сохраняем изменения
        conn.commit()

        logging.info("✅ Таблица 'test_table' успешно создана или уже существует.")

        # Закрываем курсор и соединение
        cur.close()
        conn.close()

    except Exception as e:
        logging.error(f"❌ Ошибка при создании таблицы: {e}")


# Запускаем функцию
if __name__ == "__main__":
    create_test_table()
