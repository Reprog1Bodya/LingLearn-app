from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from server.models.user import User
from server.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def update_profile(
        self,
        user: User,
        username: str | None = None,
        daily_goal: int | None = None,
        notifications: int | None = None,
        language: str | None = None,
        goal: str | None = None,
    ) -> User:
        try:
            self.users.update(
                user,
                username=username,
                daily_goal=daily_goal,
                notifications=notifications,
                language=language,
                goal=goal,
            )
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось обновить профиль: {str(e)}",
            )
