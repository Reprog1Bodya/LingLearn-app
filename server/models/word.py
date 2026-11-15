from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dict_id: Mapped[int] = mapped_column(Integer, ForeignKey("dictionaries.id", ondelete="CASCADE"), nullable=False, index=True)
    word: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    translation: Mapped[str] = mapped_column(String(256), nullable=False)
    transcription: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    example: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи ORM
    dictionary: Mapped["Dictionary"] = relationship("Dictionary", back_populates="words")
    progress_records: Mapped[list["UserWordProgress"]] = relationship("UserWordProgress", back_populates="word", cascade="all, delete-orphan")
