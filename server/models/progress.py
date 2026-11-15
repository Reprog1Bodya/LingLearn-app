from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base


class UserWordProgress(Base):
    __tablename__ = "user_word_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True)
    is_learned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    box: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_tested: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_user_word_progress"),
        CheckConstraint("is_learned IN (0, 1)", name="chk_prog_is_learned_bool"),
        CheckConstraint("box >= 0", name="chk_prog_box_positive"),
        CheckConstraint("error_count >= 0", name="chk_prog_error_positive"),
    )

    # Связи ORM
    user: Mapped["User"] = relationship("User", back_populates="word_progress")
    word: Mapped["Word"] = relationship("Word", back_populates="progress_records")


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dict_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dictionaries.id", ondelete="SET NULL"), nullable=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("score >= 0", name="chk_test_score_positive"),
        CheckConstraint("total >= score", name="chk_test_total_gte_score"),
    )

    # Связи ORM
    user: Mapped["User"] = relationship("User", back_populates="test_results")
