from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base


class Dictionary(Base):
    __tablename__ = "dictionaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lang: Mapped[str] = mapped_column(String(8), ForeignKey("languages.code", ondelete="RESTRICT"), nullable=False)
    goal: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    author_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_public: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("is_public IN (0, 1)", name="chk_dict_is_public_bool"),
        Index("ix_dictionaries_lang_goal", "lang", "goal"),
    )

    # Связи ORM
    language_rel: Mapped["Language"] = relationship("Language", back_populates="dictionaries")
    author: Mapped["User"] = relationship("User", back_populates="authored_dictionaries")
    words: Mapped[list["Word"]] = relationship("Word", back_populates="dictionary", cascade="all, delete-orphan")
    user_associations: Mapped[list["UserDictionary"]] = relationship("UserDictionary", back_populates="dictionary", cascade="all, delete-orphan")
