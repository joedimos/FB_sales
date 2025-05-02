from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings
from .models import Base # Import Base from models.py

# Database URL from settings
DATABASE_URL = settings.get("database_url")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL not found in settings.yaml")

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite with FastAPI
# For PostgreSQL/MySQL, remove this
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database: creates tables."""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized (tables created).")

if __name__ == '__main__':
    # Example of running init_db directly
    init_db()
