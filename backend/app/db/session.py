from sqlmodel import create_engine, Session, SQLModel
from pathlib import Path


#We create Path object in order to point our database file
DB_FILE = Path(__file__).resolve().parents[2] / "data" / "app.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True) #if catalog doesn't exist, create it. If it exists, it's OK

DATABASE_URL = f"sqlite:///{DB_FILE}"



engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session