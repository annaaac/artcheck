#database.py

from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, DateTime, LargeBinary, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=True)
    embedding = Column(LargeBinary, nullable=False)
    time_uploaded = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SimilarArtwork(Base):
    __tablename__ = "similar_artworks"
    __table_args__ = (
        UniqueConstraint("artwork_id", "url", name="uq_artwork_url"),
    )

    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)
    url = Column(String, nullable=False)
    similarity_score = Column(Integer, nullable=False)
    is_similar = Column(Boolean, nullable=False)
    time_scanned = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False, default="new")