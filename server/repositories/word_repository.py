from datetime import datetime, timezone
import random
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.orm import Session

from server.models.word import Word


class WordRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, word_id: int) -> Word | None:
        return self.db.execute(select(Word).where(Word.id == word_id)).scalar_one_or_none()

    def list_by_dictionary(
        self,
        dict_id: int,
        search: str | None = None,
        sort_by: str = "id",
        order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Word]:
        stmt = select(Word).where(Word.dict_id == dict_id)
        if search:
            s = f"%{search.strip()}%"
            stmt = stmt.where(Word.word.ilike(s) | Word.translation.ilike(s))

        # Сортировка с защитой от SQL-инъекций (строго сопоставление атрибутов модели)
        sort_col = getattr(Word, sort_by, Word.id)
        stmt = stmt.order_by(desc(sort_col) if order.lower() == "desc" else asc(sort_col))

        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count_by_dictionary(self, dict_id: int, search: str | None = None) -> int:
        stmt = select(func.count(Word.id)).where(Word.dict_id == dict_id)
        if search:
            s = f"%{search.strip()}%"
            stmt = stmt.where(Word.word.ilike(s) | Word.translation.ilike(s))
        return self.db.scalar(stmt) or 0

    def create(
        self,
        dict_id: int,
        word: str,
        translation: str,
        transcription: str = "",
        example: str = "",
    ) -> Word:
        w = Word(
            dict_id=dict_id,
            word=word.strip(),
            translation=translation.strip(),
            transcription=transcription.strip(),
            example=example.strip(),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(w)
        self.db.flush()
        return w

    def update(self, word_obj: Word, **kwargs) -> Word:
        for k, v in kwargs.items():
            if v is not None and hasattr(word_obj, k):
                setattr(word_obj, k, v.strip() if isinstance(v, str) else v)
        self.db.flush()
        return word_obj

    def delete(self, word_obj: Word) -> None:
        self.db.delete(word_obj)
        self.db.flush()

    def random_words_from_dictionary(self, dict_id: int, limit: int = 20) -> list[Word]:
        words = list(self.db.execute(select(Word).where(Word.dict_id == dict_id)).scalars().all())
        random.shuffle(words)
        return words[:limit]

    def random_translations_excluding_dict(self, dict_id: int, limit: int = 15) -> list[str]:
        stmt = select(Word.translation).where(Word.dict_id != dict_id).distinct().limit(limit * 2)
        translations = list(self.db.execute(stmt).scalars().all())
        random.shuffle(translations)
        return translations[:limit]

    def count(self) -> int:
        return self.db.scalar(select(func.count(Word.id))) or 0
