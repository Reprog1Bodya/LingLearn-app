from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from server.models.language import Language, LanguageFeature


class LanguageRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Language]:
        return list(self.db.execute(select(Language).order_by(Language.name.asc())).scalars().all())

    def get_by_code(self, code: str) -> Language | None:
        return self.db.execute(select(Language).where(Language.code == code)).scalar_one_or_none()

    def list_features(self, lang_code: str) -> list[LanguageFeature]:
        stmt = (
            select(LanguageFeature)
            .where(LanguageFeature.lang_code == lang_code)
            .order_by(LanguageFeature.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_language(self, code: str, name: str, native: str, niche: int = 0, flag: str = "") -> Language:
        lang = Language(code=code, name=name, native=native, niche=niche, flag=flag)
        self.db.add(lang)
        self.db.flush()
        return lang

    def create_feature(self, lang_code: str, title: str, body: str) -> LanguageFeature:
        feat = LanguageFeature(lang_code=lang_code, title=title, body=body)
        self.db.add(feat)
        self.db.flush()
        return feat
