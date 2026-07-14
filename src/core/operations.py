from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Engine
from dotenv import load_dotenv  # loads env
import os
from collections.abc import Generator
from .schema import Base
from sqlalchemy.pool import NullPool

# Import every model so SQLAlchemy registers the tables on Base.metadata.

# Importing the models ensures they are registered with Base.metadata.
from .schema import (
    HVACAnalysis,
    HVACSubmission,
    WaterHeaterAnalysis,
    WaterHeaterSubmission,
)

load_dotenv()


DATABASE_URL = os.environ["DATABASE_URL"]

ENGINE: Engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 10,
        "sslmode": "require",
        "prepare_threshold": None,
    },
)

SessionLocal = sessionmaker(
    bind=ENGINE,
    autocommit=False,
    autoflush=False,
)


# Creates tables
def init_tables(engine: Engine) -> None:
    print("Tables found:", list(Base.metadata.tables.keys()))
    print("Testing database connection...")

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Database connection successful.")
    print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    print("Tables created successfully.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()