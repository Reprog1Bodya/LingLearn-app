from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.models.user import User
from server.models.word import Word
from server.repositories.word_repository import WordRepository
from server.repositories.dictionary_repository import DictionaryRepository
from server.repositories.progress_repository import ProgressRepository


class WordService:
    def __init__(self, db: Session):
        self.db = db
        self.words = WordRepository(db)
        self.dicts = DictionaryRepository(db)
        self.progress = ProgressRepository(db)

    def list_dictionary_words(
        self,
        dict_id: int,
        search: str | None = None,
        sort_by: str = "id",
        order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        total = self.words.count_by_dictionary(dict_id, search=search)
        word_objs = self.words.list_by_dictionary(
            dict_id=dict_id,
            search=search,
            sort_by=sort_by,
            order=order,
            limit=limit,
            offset=offset,
        )
        res = [
            {
                "id": w.id,
                "dict_id": w.dict_id,
                "word": w.word,
                "translation": w.translation,
                "transcription": w.transcription,
                "example": w.example,
                "learned": 0,
            }
            for w in word_objs
        ]
        return res, total

    def list_my_words(
        self,
        user_id: int,
        filter_type: str | None = None,
        search: str | None = None,
        sort_by: str = "id",
        order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        total = self.progress.count_my_words(user_id, filter_type=filter_type, search=search)
        pairs = self.progress.list_my_words(
            user_id=user_id,
            filter_type=filter_type,
            search=search,
            sort_by=sort_by,
            order=order,
            limit=limit,
            offset=offset,
        )
        res = [
            {
                "id": w.id,
                "dict_id": w.dict_id,
                "word": w.word,
                "translation": w.translation,
                "transcription": w.transcription,
                "example": w.example,
                "learned": learned,
            }
            for w, learned in pairs
        ]
        return res, total

    def get_by_id(self, word_id: int) -> Word:
        w = self.words.get_by_id(word_id)
        if not w:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Слово не найдено",
            )
        return w

    def create_word(
        self,
        current_user: User,
        dict_id: int | None,
        word: str,
        translation: str,
        transcription: str = "",
        example: str = "",
    ) -> Word:
        """Создание слова с проверкой прав и атомарным управлением транзакцией."""
        target_dict_id = dict_id
        try:
            # Если dict_id не указан, используем или создаём личный словарь пользователя
            if not target_dict_id:
                p_dict = self.dicts.get_personal_dictionary(current_user.id)
                if not p_dict:
                    p_dict = self.dicts.create(
                        lang=current_user.language or "en",
                        goal=current_user.goal or "travel",
                        title="Мой словарь",
                        description="Личные слова пользователя",
                        author_id=current_user.id,
                        is_public=False,
                    )
                    self.dicts.add_user_dictionary(current_user.id, p_dict.id)
                target_dict_id = p_dict.id
            else:
                d = self.dicts.get_by_id(target_dict_id)
                if not d:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Указанный словарь не существует",
                    )
                # Если словарь чужой и не публичный и пользователь не админ: запрет
                if d.author_id != current_user.id and current_user.role != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="У вас нет прав на добавление слов в этот словарь",
                    )

            # Создание слова
            w = self.words.create(
                dict_id=target_dict_id,
                word=word,
                translation=translation,
                transcription=transcription,
                example=example,
            )
            # Отслеживание в прогрессе
            self.progress.get_or_create_word_progress(current_user.id, w.id)

            self.db.commit()
            self.db.refresh(w)
            return w
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось создать слово: {str(e)}",
            )

    def update_word(
        self,
        word_id: int,
        current_user: User,
        word: str | None = None,
        translation: str | None = None,
        transcription: str | None = None,
        example: str | None = None,
    ) -> Word:
        """Редактирование слова с проверкой принадлежности автору словаря."""
        w = self.get_by_id(word_id)
        d = self.dicts.get_by_id(w.dict_id)

        # Проверка прав: редактировать слово может только владелец словаря или админ
        if d and d.author_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на редактирование этого слова",
            )

        try:
            self.words.update(
                w,
                word=word,
                translation=translation,
                transcription=transcription,
                example=example,
            )
            self.db.commit()
            self.db.refresh(w)
            return w
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось обновить слово: {str(e)}",
            )

    def delete_word(self, word_id: int, current_user: User) -> None:
        """Удаление слова с проверкой принадлежности автору словаря."""
        w = self.get_by_id(word_id)
        d = self.dicts.get_by_id(w.dict_id)

        # Проверка прав: удалять слово может только владелец словаря или админ
        if d and d.author_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на удаление этого слова",
            )

        try:
            self.words.delete(w)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось удалить слово: {str(e)}",
            )

    def set_learned(self, word_id: int, user_id: int, learned: bool) -> None:
        self.get_by_id(word_id)
        try:
            self.progress.set_word_learned(user_id, word_id, learned)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось изменить статус слова",
            )
