from config import SessionLocal
from sqlalchemy.sql import text  # Добавляем импорт text()

def test_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # Исправленный запрос
        print("✅ Успешное подключение к базе данных!")
    except Exception as e:
        print("❌ Ошибка подключения:", e)
    finally:
        db.close()

test_db_connection()
