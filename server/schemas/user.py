from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: str
    language: str | None = None
    goal: str = "travel"
    daily_goal: int = 10
    notifications: int = 1
    streak: int = 0
    points: int = 0
    last_active: str = ""


class UserUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=64)
    daily_goal: int | None = Field(default=None, ge=1, le=200)
    notifications: int | None = Field(default=None, ge=0, le=1)
    language: str | None = None
    goal: str | None = None


class UserPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    email: str
    created_at: datetime
