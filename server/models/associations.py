from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base


class UserDictionary(Base):
    """Промежуточная таблица связи N:M между User и Dictionary.
    Пользователь может подключать множество словарей,
    а словарь может быть подключён множеством пользователей.
    """
    __tablename__ = "user_dictionaries"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dict_id: Mapped[int] = mapped_column(Integer, ForeignKey("dictionaries.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи ORM
    user: Mapped["User"] = relationship("User", back_populates="dictionaries")
    dictionary: Mapped["Dictionary"] = relationship("Dictionary", back_populates="user_associations")
