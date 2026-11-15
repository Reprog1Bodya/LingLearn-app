from sqlalchemy import String, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.models.base import Base


class Language(Base):
    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    native: Mapped[str] = mapped_column(String(64), nullable=False)
    niche: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flag: Mapped[str] = mapped_column(String(16), default="", nullable=False)

    __table_args__ = (
        CheckConstraint("niche IN (0, 1)", name="chk_lang_niche_bool"),
    )

    # Связи ORM
    features: Mapped[list["LanguageFeature"]] = relationship("LanguageFeature", back_populates="language", cascade="all, delete-orphan")
    dictionaries: Mapped[list["Dictionary"]] = relationship("Dictionary", back_populates="language_rel")


class LanguageFeature(Base):
    __tablename__ = "language_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lang_code: Mapped[str] = mapped_column(String(8), ForeignKey("languages.code", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Связь ORM
    language: Mapped["Language"] = relationship("Language", back_populates="features")
