from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from server.models.token import RevokedToken


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def is_revoked(self, jti: str) -> bool:
        stmt = select(RevokedToken).where(RevokedToken.jti == jti)
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def revoke(self, jti: str, expires_at: datetime) -> RevokedToken:
        token = RevokedToken(jti=jti, expires_at=expires_at)
        self.db.add(token)
        self.db.flush()
        return token

    def purge_expired(self) -> int:
        stmt = delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(timezone.utc))
        res = self.db.execute(stmt)
        self.db.flush()
        return res.rowcount
