from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Engine
from dotenv import load_dotenv  # loads env
import os
from collections.abc import Generator
from .models import Base

# Import every model so SQLAlchemy registers the tables on Base.metadata.

# Importing the models ensures they are registered with Base.metadata.

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./applianceiq_local.db",
)


if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Creates tables
def init_tables(engine: Engine) -> None:
    print("Tables found:", list(Base.metadata.tables.keys()))
    print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    print("Tables created successfully.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
