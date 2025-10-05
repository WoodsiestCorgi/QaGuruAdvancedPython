
import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlmodel import create_engine, SQLModel

# fake_db: dict[str, User] = {}

db_engine = create_engine(os.getenv("DATABASE_ENGINE"), pool_size=os.getenv("DATABASE_POOL_SIZE", 10))

def create_db_and_tables():
    SQLModel.metadata.create_all(db_engine)

def check_availability() -> bool:
    try:
        with Session(db_engine) as session:
            session.execute(text("SELECT 1"))
        return True

    except Exception as e:
        print(e)
        return False


def reset_user_sequence():
    """Сбрасывает sequence для таблицы user, чтобы избежать конфликтов с явно указанными id"""
    try:
        with Session(db_engine) as session:
            # Устанавливаем sequence на максимальный существующий id + 1
            session.execute(text("SELECT setval(pg_get_serial_sequence('user', 'id'), COALESCE((SELECT MAX(id) FROM \"user\"), 1), true)"))
            session.commit()
    except Exception as e:
        print(f"Error resetting sequence: {e}")
