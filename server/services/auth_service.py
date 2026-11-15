import logging
import uuid
from datetime import timezone, datetime, timedelta
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from server.database.config import settings
from server.database.connection import get_db
from server.models.user import User
from server.repositories.user_repository import UserRepository
from server.repositories.token_repository import TokenRepository

security_bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("linglearn")


def hash_password(password: str) -> str:
    """Хеширование пароля с помощью bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка соответствия пароля хешу."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user: User, expires_delta: timedelta | None = None) -> tuple[str, str]:
    """Создание JWT токена с ограниченным сроком действия и уникальным jti."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    def register(self, email: str, username: str, password: str) -> tuple[User, str]:
        # Проверка дубликата на уровне приложения
        existing = self.users.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            )

        hashed = hash_password(password)
        try:
            user = self.users.create(email=email, username=username, password_hash=hashed)
            self.db.commit()
            self.db.refresh(user)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Не удалось зарегистрировать пользователя (возможно email уже занят)",
            )

        token, _ = create_access_token(user)
        return user, token

    def login(self, email: str, password: str) -> tuple[User, str]:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token, _ = create_access_token(user)
        return user, token

    def logout(self, token_str: str) -> None:
        try:
            payload = jwt.decode(
                token_str,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp, timezone.utc)
                self.tokens.revoke(jti, expires_at)
                self.db.commit()
        except Exception:
            pass

    def request_password_reset(self, email: str) -> str | None:
        """Создаёт одноразовый код. Для несуществующего email ничего не делает и не сообщает об этом
        (иначе по ответу API можно перебирать зарегистрированные адреса)."""
        user = self.users.get_by_email(email)
        if not user:
            return None
        import secrets
        code = "%06d" % secrets.randbelow(10**6)
        self.users.save_reset_code(email, code, settings.RESET_CODE_TTL_MINUTES)
        self.db.commit()
        # Заглушка SMTP: код попадает только в серверный журнал, а не в ответ API.
        logger.warning("[SMTP-заглушка] Код восстановления для %s: %s (действует %d мин.)",
                       email, code, settings.RESET_CODE_TTL_MINUTES)
        return code

    def confirm_password_reset(self, email: str, code: str, new_password: str) -> None:
        user = self.users.verify_and_clear_reset_code(email, code)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или устаревший код восстановления",
            )
        user.password_hash = hash_password(new_password)
        self.db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI зависимость для проверки JWT и получения текущего пользователя."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация (отсутствует Bearer токен)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        jti = payload.get("jti")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истёк. Пожалуйста, выполните вход снова",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен авторизации",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверка, не отозван ли токен
    tokens_repo = TokenRepository(db)
    if jti and tokens_repo.is_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен был отозван. Выполните вход снова",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users_repo = UserRepository(db)
    user = users_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI зависимость для проверки прав администратора."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции (требуется роль admin)",
        )
    return current_user
