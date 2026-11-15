from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.models.user import User
from server.repositories.user_repository import UserRepository
from server.repositories.dictionary_repository import DictionaryRepository
from server.repositories.word_repository import WordRepository
from server.repositories.progress_repository import ProgressRepository


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.dicts = DictionaryRepository(db)
        self.words = WordRepository(db)
        self.progress = ProgressRepository(db)

    def get_analytics(self) -> dict:
        return {
            "users": self.users.count(),
            "dictionaries": self.dicts.count(),
            "words": self.words.count(),
            "tests": self.progress.tests_count(),
        }

    def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        return self.users.list_all(limit=limit, offset=offset)

    def delete_user(self, target_user_id: int, current_admin: User) -> None:
        if target_user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить собственную учетную запись администратора",
            )
        target = self.users.get_by_id(target_user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
        try:
            self.users.delete(target)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось удалить пользователя: {str(e)}",
            )
