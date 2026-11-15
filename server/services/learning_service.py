import random
import time
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.models.user import User
from server.repositories.word_repository import WordRepository
from server.repositories.dictionary_repository import DictionaryRepository
from server.repositories.progress_repository import ProgressRepository
from server.repositories.user_repository import UserRepository


class LearningService:
    def __init__(self, db: Session):
        self.db = db
        self.words = WordRepository(db)
        self.dicts = DictionaryRepository(db)
        self.progress = ProgressRepository(db)
        self.users = UserRepository(db)

    def generate_test(self, dict_id: int, kind: str = "translate", count: int = 8) -> dict:
        d = self.dicts.get_by_id(dict_id)
        if not d:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Словарь не найден",
            )

        ws = self.words.random_words_from_dictionary(dict_id, limit=max(count, 4))
        if len(ws) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="В словаре слишком мало слов для проведения теста (нужно минимум 2)",
            )

        foreign_pool = self.words.random_translations_excluding_dict(dict_id, limit=10)
        questions = []
        for w in ws[:count]:
            other_options = [x.translation for x in ws if x.id != w.id] + foreign_pool
            random.shuffle(other_options)
            # Убираем дубликаты
            opts = list(dict.fromkeys([o for o in other_options if o != w.translation]))[:3]
            opts.append(w.translation)
            random.shuffle(opts)

            questions.append(
                {
                    "word_id": w.id,
                    "word": w.word,
                    "transcription": w.transcription,
                    "answer": w.translation,
                    "example": w.example,
                    "options": opts,
                }
            )

        return {"kind": kind, "questions": questions}

    def submit_test_result(
        self,
        current_user: User,
        dict_id: int | None,
        kind: str,
        score: int,
        total: int,
        answers: dict[str, bool],
    ) -> dict:
        """Атомарная многошаговая транзакция сохранения результатов тренировки."""
        today = time.strftime("%Y-%m-%d")
        try:
            # 1. Сохранение записи результата теста
            self.progress.save_test_result(
                user_id=current_user.id,
                dict_id=dict_id,
                kind=kind,
                score=score,
                total=total,
            )

            # 2. Обновление прогресса каждого слова
            for wid_str, ok in answers.items():
                try:
                    wid = int(wid_str)
                    self.progress.record_answer(current_user.id, wid, bool(ok))
                except (ValueError, TypeError):
                    continue

            # 3. Начисление очков и подсчет серии дней
            pts_earned = int(score) * 10
            streak = current_user.streak
            if current_user.last_active != today:
                yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
                if current_user.last_active == yesterday:
                    streak += 1
                else:
                    streak = 1

            self.users.update(
                current_user,
                points=current_user.points + pts_earned,
                streak=streak,
                last_active=today,
            )

            # Фиксация единой транзакции
            self.db.commit()
            return {"points": pts_earned, "streak": streak}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось сохранить результаты тренировки: {str(e)}",
            )

    def get_stats(self, current_user: User) -> dict:
        st = self.progress.get_user_stats(current_user.id)
        st["streak"] = current_user.streak
        st["points"] = current_user.points
        return st
