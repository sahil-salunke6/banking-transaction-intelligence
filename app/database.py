
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATABASE_URL = (
    f"sqlite:///{PROJECT_ROOT / 'banking_transactions.db'}"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()
