import re
from pydantic import BaseModel, Field, field_validator, model_validator
from server.schemas.user import UserProfileResponse

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserRegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=128)
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    password_confirm: str | None = Field(default=None, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Некорректный формат email адреса")
        return v_clean

    @model_validator(mode="after")
    def verify_password_match(self):
        if self.password_confirm is not None and self.password != self.password_confirm:
            raise ValueError("Пароли не совпадают")
        return self


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=128)
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Некорректный формат email адреса")
        return v_clean


class TokenResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    profile: UserProfileResponse


class PasswordRecoverRequest(BaseModel):
    email: str = Field(min_length=5, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Некорректный формат email адреса")
        return v_clean


class PasswordRecoverResponse(BaseModel):
    message: str
    demo_code: str | None = None


class PasswordRecoverConfirmRequest(BaseModel):
    email: str = Field(min_length=5, max_length=128)
    code: str = Field(min_length=4, max_length=16)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Некорректный формат email адреса")
        return v_clean
