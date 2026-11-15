from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.models.user import User
from server.models.dictionary import Dictionary
from server.repositories.dictionary_repository import DictionaryRepository
from server.repositories.language_repository import LanguageRepository


class DictionaryService:
    def __init__(self, db: Session):
        self.db = db
        self.dicts = DictionaryRepository(db)
        self.langs = LanguageRepository(db)

    def list_dictionaries(
        self,
        current_user: User | None = None,
        lang: str | None = None,
        goal: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        user_dict_ids = set()
        user_goal = current_user.goal if current_user else None
        if current_user:
            user_dict_ids = self.dicts.get_user_dictionary_ids(current_user.id)

        all_dicts = self.dicts.list_all(
            lang=lang,
            goal=goal,
            search=search,
            is_public=True,
            limit=limit,
            offset=offset,
        )

        res = []
        for d in all_dicts:
            is_added = 1 if d.id in user_dict_ids else 0
            is_rec = bool(user_goal and d.goal == user_goal)
            res.append(
                {
                    "id": d.id,
                    "lang": d.lang,
                    "goal": d.goal,
                    "title": d.title,
                    "descr": d.description,
                    "cnt": len(d.words),
                    "added": is_added,
                    "recommended": is_rec,
                    "author_id": d.author_id,
                }
            )
        return res

    def get_by_id(self, dict_id: int) -> Dictionary:
        d = self.dicts.get_by_id(dict_id)
        if not d:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Словарь не найден",
            )
        return d

    def create_dictionary(
        self,
        current_user: User,
        lang: str,
        goal: str,
        title: str,
        description: str = "",
        is_public: bool = True,
    ) -> Dictionary:
        if not self.langs.get_by_code(lang):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Язык '{lang}' не поддерживается",
            )
        try:
            d = self.dicts.create(
                lang=lang,
                goal=goal,
                title=title,
                description=description,
                author_id=current_user.id,
                is_public=is_public,
            )
            self.db.commit()
            self.db.refresh(d)
            return d
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось создать словарь",
            )

    def update_dictionary(
        self,
        dict_id: int,
        current_user: User,
        title: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> Dictionary:
        d = self.get_by_id(dict_id)
        # Проверка прав: редактировать словарь может автор или админ
        if d.author_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на редактирование этого словаря",
            )
        try:
            self.dicts.update(d, title=title, description=description, is_public=is_public)
            self.db.commit()
            self.db.refresh(d)
            return d
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось обновить словарь",
            )

    def delete_dictionary(self, dict_id: int, current_user: User) -> None:
        d = self.get_by_id(dict_id)
        # Проверка прав: удалять словарь может автор или админ
        if d.author_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на удаление этого словаря",
            )
        try:
            self.dicts.delete(d)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось удалить словарь",
            )

    def toggle_user_dictionary(self, user_id: int, dict_id: int, add: bool) -> bool:
        self.get_by_id(dict_id)
        try:
            if add:
                self.dicts.add_user_dictionary(user_id, dict_id)
            else:
                self.dicts.remove_user_dictionary(user_id, dict_id)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
