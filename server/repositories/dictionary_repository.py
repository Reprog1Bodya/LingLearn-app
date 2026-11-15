from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload

from server.models.dictionary import Dictionary
from server.models.word import Word
from server.models.associations import UserDictionary


class DictionaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, dict_id: int) -> Dictionary | None:
        stmt = (
            select(Dictionary)
            .where(Dictionary.id == dict_id)
            .options(selectinload(Dictionary.words))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        lang: str | None = None,
        goal: str | None = None,
        search: str | None = None,
        author_id: int | None = None,
        is_public: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Dictionary]:
        stmt = select(Dictionary).options(selectinload(Dictionary.words))
        conditions = []
        if lang:
            conditions.append(Dictionary.lang == lang)
        if goal:
            conditions.append(Dictionary.goal == goal)
        if author_id is not None:
            conditions.append(Dictionary.author_id == author_id)
        if is_public is not None:
            conditions.append(Dictionary.is_public == (1 if is_public else 0))
        if search:
            s = f"%{search.strip()}%"
            conditions.append(Dictionary.title.ilike(s) | Dictionary.description.ilike(s))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Dictionary.id.asc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count(self, lang: str | None = None, goal: str | None = None) -> int:
        stmt = select(func.count(Dictionary.id))
        conditions = []
        if lang:
            conditions.append(Dictionary.lang == lang)
        if goal:
            conditions.append(Dictionary.goal == goal)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return self.db.scalar(stmt) or 0

    def create(
        self,
        lang: str,
        goal: str,
        title: str,
        description: str = "",
        author_id: int | None = None,
        is_public: bool = True,
    ) -> Dictionary:
        d = Dictionary(
            lang=lang,
            goal=goal,
            title=title.strip(),
            description=description.strip(),
            author_id=author_id,
            is_public=1 if is_public else 0,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(d)
        self.db.flush()
        return d

    def update(self, dict_obj: Dictionary, **kwargs) -> Dictionary:
        for k, v in kwargs.items():
            if v is not None and hasattr(dict_obj, k):
                if k == "is_public" and isinstance(v, bool):
                    setattr(dict_obj, k, 1 if v else 0)
                else:
                    setattr(dict_obj, k, v)
        self.db.flush()
        return dict_obj

    def delete(self, dict_obj: Dictionary) -> None:
        self.db.delete(dict_obj)
        self.db.flush()

    def get_user_dictionary_ids(self, user_id: int) -> set[int]:
        stmt = select(UserDictionary.dict_id).where(UserDictionary.user_id == user_id)
        return set(self.db.execute(stmt).scalars().all())

    def add_user_dictionary(self, user_id: int, dict_id: int) -> UserDictionary:
        existing = self.db.execute(
            select(UserDictionary).where(
                and_(UserDictionary.user_id == user_id, UserDictionary.dict_id == dict_id)
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        link = UserDictionary(user_id=user_id, dict_id=dict_id, added_at=datetime.now(timezone.utc))
        self.db.add(link)
        self.db.flush()
        return link

    def remove_user_dictionary(self, user_id: int, dict_id: int) -> bool:
        link = self.db.execute(
            select(UserDictionary).where(
                and_(UserDictionary.user_id == user_id, UserDictionary.dict_id == dict_id)
            )
        ).scalar_one_or_none()
        if link:
            self.db.delete(link)
            self.db.flush()
            return True
        return False

    def get_personal_dictionary(self, user_id: int) -> Dictionary | None:
        stmt = select(Dictionary).where(
            and_(Dictionary.author_id == user_id, Dictionary.is_public == 0)
        )
        return self.db.execute(stmt).scalars().first()
