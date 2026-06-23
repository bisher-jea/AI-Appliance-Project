from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Engine
from core.schema import Base
# from dotenv import load_dotenv # loads env
import os
from collections.abc import Generator

# import from schema.py; base contains all table definitions
# load_dotenv() # loads .env variables into python !!!!!PAY EXTRA CAUTION!!!

ENGINE = create_engine(os.getenv("DB_URL", "sqlite:///sqlite.db"))
# creates db connection

# creates db session factory
SESSION_LOCAL = sessionmaker(
    autocommit=False,     # changes not auto saved
    autoflush=False,
    bind=ENGINE
)


# creates all tables in schema
def init_tables(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


# db session for each request
def get_db() -> Generator[Session, None, None]:
    with SESSION_LOCAL() as session:
        yield session


if __name__ == "__main__":
    init_tables(ENGINE)
