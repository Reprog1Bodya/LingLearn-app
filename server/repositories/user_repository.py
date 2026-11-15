import hmac
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from server.models.user import User


def _utcnow() -> datetime:
    """Текущее UTC-время без tzinfo (столбцы DateTime в моделях — naive UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User).where(func.lower(User.email) == email.strip().lower())
        ).scalar_one_or_none()

    def create(self, email: str, username: str, password_hash: str, role: str = "user") -> User:
        user = User(
            email=email.strip().lower(),
            username=username.strip(),
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User, **kwargs) -> User:
        for k, v in kwargs.items():
            if v is not None and hasattr(user, k):
                setattr(user, k, v)
        user.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.id.asc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.scalar(select(func.count(User.id))) or 0

    def save_reset_code(self, email: str, code: str, ttl_minutes: int) -> bool:
        user = self.get_by_email(email)
        if not user:
            return False
        user.reset_code = code
        user.reset_code_expires_at = _utcnow() + timedelta(minutes=ttl_minutes)
        self.db.flush()
        return True

    def verify_and_clear_reset_code(self, email: str, code: str) -> User | None:
        """Код одноразовый и ограничен по времени; сравнение выполняется за константное время."""
        user = self.get_by_email(email)
        if not user or not user.reset_code or not user.reset_code_expires_at:
            return None
        if user.reset_code_expires_at < _utcnow():
            user.reset_code = None
            user.reset_code_expires_at = None
            self.db.flush()
            return None
        if not hmac.compare_digest(user.reset_code, code):
            return None
        user.reset_code = None
        user.reset_code_expires_at = None
        self.db.flush()
        return user
