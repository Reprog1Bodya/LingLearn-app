from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from server.database.config import settings

from server.database.connection import get_db
from server.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    PasswordRecoverRequest,
    PasswordRecoverResponse,
    PasswordRecoverConfirmRequest,
)
from server.schemas.common import MessageResponse
from server.schemas.user import UserProfileResponse
from server.services.auth_service import AuthService, security_bearer

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
def register(
    data: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user, token = service.register(
        email=data.email,
        username=data.username,
        password=data.password,
    )
    return TokenResponse(token=token, profile=UserProfileResponse.model_validate(user))


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Авторизация пользователя и получение JWT",
)
def login(
    data: UserLoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user, token = service.login(email=data.email, password=data.password)
    return TokenResponse(token=token, profile=UserProfileResponse.model_validate(user))


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Выход из системы (отзыв текущего токена)",
)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_db),
):
    if credentials and credentials.credentials:
        service = AuthService(db)
        service.logout(credentials.credentials)
    return MessageResponse(message="Успешный выход из системы")


@router.post(
    "/recover",
    response_model=PasswordRecoverResponse,
    status_code=status.HTTP_200_OK,
    summary="Запрос кода для сброса пароля",
)
def recover_password(
    data: PasswordRecoverRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    code = service.request_password_reset(data.email)
    # Ответ одинаков для существующих и несуществующих email; код в ответ попадает только в DEV-режиме
    return PasswordRecoverResponse(
        message="Если указанный email зарегистрирован, код восстановления отправлен на почту",
        demo_code=code if settings.DEV_EXPOSE_RESET_CODE else None,
    )


@router.post(
    "/recover/confirm",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Подтверждение кода и установка нового пароля",
)
def recover_password_confirm(
    data: PasswordRecoverConfirmRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.confirm_password_reset(
        email=data.email,
        code=data.code,
        new_password=data.password,
    )
    return MessageResponse(message="Пароль успешно обновлён")
