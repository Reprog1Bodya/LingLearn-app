from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="user", nullable=False)
    language: Mapped[str | None] = mapped_column(String(8), ForeignKey("languages.code", ondelete="SET NULL"), nullable=True)
    goal: Mapped[str] = mapped_column(String(32), default="travel", nullable=False)
    daily_goal: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    notifications: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    reset_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reset_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("length(email) >= 5", name="chk_user_email_len"),
        CheckConstraint("length(username) >= 2", name="chk_user_username_len"),
        CheckConstraint("streak >= 0", name="chk_user_streak_positive"),
        CheckConstraint("points >= 0", name="chk_user_points_positive"),
        CheckConstraint("daily_goal >= 1 AND daily_goal <= 200", name="chk_user_daily_goal_range"),
        CheckConstraint("notifications IN (0, 1)", name="chk_user_notifications_bool"),
    )

    # Связи ORM
    dictionaries: Mapped[list["UserDictionary"]] = relationship("UserDictionary", back_populates="user", cascade="all, delete-orphan")
    word_progress: Mapped[list["UserWordProgress"]] = relationship("UserWordProgress", back_populates="user", cascade="all, delete-orphan")
    test_results: Mapped[list["TestResult"]] = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")
    authored_dictionaries: Mapped[list["Dictionary"]] = relationship("Dictionary", back_populates="author")
