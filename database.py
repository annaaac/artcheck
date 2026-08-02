#database.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///artcheck.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=True)
    embedding = Column(LargeBinary, nullable=False)
    upload_time = Column(DateTime, default=datetime.now(timezone.utc))


def start_db():
    Base.metadata.create_all(engine)