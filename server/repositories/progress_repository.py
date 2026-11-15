from datetime import datetime, timezone
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.orm import Session, joinedload

from server.models.progress import UserWordProgress, TestResult
from server.models.word import Word
from server.models.dictionary import Dictionary
from server.models.associations import UserDictionary


class ProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_word_progress(self, user_id: int, word_id: int) -> UserWordProgress:
        stmt = select(UserWordProgress).where(
            and_(UserWordProgress.user_id == user_id, UserWordProgress.word_id == word_id)
        )
        prog = self.db.execute(stmt).scalar_one_or_none()
        if not prog:
            prog = UserWordProgress(
                user_id=user_id,
                word_id=word_id,
                is_learned=0,
                box=0,
                error_count=0,
                last_tested=None,
            )
            self.db.add(prog)
            self.db.flush()
        return prog

    def set_word_learned(self, user_id: int, word_id: int, is_learned: bool) -> UserWordProgress:
        prog = self.get_or_create_word_progress(user_id, word_id)
        prog.is_learned = 1 if is_learned else 0
        self.db.flush()
        return prog

    def list_my_words(
        self,
        user_id: int,
        filter_type: str | None = None,  # "all", "learned", "unlearned"
        search: str | None = None,
        sort_by: str = "id",
        order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[Word, int]]:
        """Возвращает слова из личного словаря пользователя и словарей, которые он подключил,
        с отметкой learned (1/0).
        Использует joinedload для эффективной выборки без N+1.
        """
        # Все доступные пользователю слова: из личного словаря + из подключенных словарей
        user_dict_ids_subq = (
            select(UserDictionary.dict_id)
            .where(UserDictionary.user_id == user_id)
            .scalar_subquery()
        )
        personal_dict_id_subq = (
            select(Dictionary.id)
            .where(and_(Dictionary.author_id == user_id, Dictionary.is_public == 0))
            .scalar_subquery()
        )

        stmt = (
            select(Word, func.coalesce(UserWordProgress.is_learned, 0).label("learned"))
            .outerjoin(
                UserWordProgress,
                and_(UserWordProgress.word_id == Word.id, UserWordProgress.user_id == user_id),
            )
            .where(
                Word.dict_id.in_(user_dict_ids_subq) | Word.dict_id.in_(personal_dict_id_subq)
            )
        )

        if filter_type == "learned":
            stmt = stmt.where(UserWordProgress.is_learned == 1)
        elif filter_type == "unlearned":
            stmt = stmt.where(
                (UserWordProgress.is_learned == 0) | (UserWordProgress.is_learned.is_(None))
            )

        if search:
            s = f"%{search.strip()}%"
            stmt = stmt.where(Word.word.ilike(s) | Word.translation.ilike(s))

        sort_col = getattr(Word, sort_by, Word.id)
        stmt = stmt.order_by(desc(sort_col) if order.lower() == "desc" else asc(sort_col))
        stmt = stmt.limit(limit).offset(offset)

        results = self.db.execute(stmt).all()
        return [(row[0], int(row[1])) for row in results]

    def count_my_words(
        self,
        user_id: int,
        filter_type: str | None = None,
        search: str | None = None,
    ) -> int:
        user_dict_ids_subq = (
            select(UserDictionary.dict_id)
            .where(UserDictionary.user_id == user_id)
            .scalar_subquery()
        )
        personal_dict_id_subq = (
            select(Dictionary.id)
            .where(and_(Dictionary.author_id == user_id, Dictionary.is_public == 0))
            .scalar_subquery()
        )

        stmt = (
            select(func.count(Word.id))
            .outerjoin(
                UserWordProgress,
                and_(UserWordProgress.word_id == Word.id, UserWordProgress.user_id == user_id),
            )
            .where(
                Word.dict_id.in_(user_dict_ids_subq) | Word.dict_id.in_(personal_dict_id_subq)
            )
        )

        if filter_type == "learned":
            stmt = stmt.where(UserWordProgress.is_learned == 1)
        elif filter_type == "unlearned":
            stmt = stmt.where(
                (UserWordProgress.is_learned == 0) | (UserWordProgress.is_learned.is_(None))
            )

        if search:
            s = f"%{search.strip()}%"
            stmt = stmt.where(Word.word.ilike(s) | Word.translation.ilike(s))

        return self.db.scalar(stmt) or 0

    def save_test_result(
        self,
        user_id: int,
        dict_id: int | None,
        kind: str,
        score: int,
        total: int,
    ) -> TestResult:
        res = TestResult(
            user_id=user_id,
            dict_id=dict_id,
            kind=kind,
            score=score,
            total=total,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(res)
        self.db.flush()
        return res

    def record_answer(self, user_id: int, word_id: int, is_correct: bool) -> None:
        prog = self.get_or_create_word_progress(user_id, word_id)
        prog.last_tested = datetime.now(timezone.utc)
        if is_correct:
            prog.box = min(prog.box + 1, 5)
            if prog.box >= 4:
                prog.is_learned = 1
        else:
            prog.box = max(0, prog.box - 1)
            prog.error_count += 1
            prog.is_learned = 0
        self.db.flush()

    def get_user_stats(self, user_id: int) -> dict:
        # Всего слов в подключенных словарях
        total_words = self.count_my_words(user_id)
        learned_words = self.count_my_words(user_id, filter_type="learned")

        # Тренировки
        stmt_tests = select(
            func.count(TestResult.id),
            func.coalesce(func.sum(TestResult.score), 0),
            func.coalesce(func.sum(TestResult.total), 0),
        ).where(TestResult.user_id == user_id)
        tests_cnt, correct_cnt, questions_cnt = self.db.execute(stmt_tests).one()

        # История последних 10 тренировок
        stmt_hist = (
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .order_by(TestResult.created_at.desc())
            .limit(10)
        )
        history_rows = self.db.execute(stmt_hist).scalars().all()
        history = [
            {
                "id": r.id,
                "kind": r.kind,
                "score": r.score,
                "total": r.total,
                "created": int(r.created_at.timestamp()),
            }
            for r in history_rows
        ]

        return {
            "words": total_words,
            "learned": learned_words,
            "tests": int(tests_cnt or 0),
            "questions": int(questions_cnt or 0),
            "correct": int(correct_cnt or 0),
            "history": history,
        }

    def tests_count(self) -> int:
        return self.db.scalar(select(func.count(TestResult.id))) or 0
