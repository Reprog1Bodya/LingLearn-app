from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.database.connection import get_db
from server.models.user import User
from server.schemas.user import UserProfileResponse, UserUpdateRequest
from server.schemas.learning import StatsResponse
from server.services.auth_service import get_current_user
from server.services.user_service import UserService
from server.services.learning_service import LearningService

router = APIRouter(tags=["Users & Profile"])


class LanguageUpdateRequest(BaseModel):
    language: str


class GoalUpdateRequest(BaseModel):
    goal: str


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение профиля текущего пользователя",
)
def get_profile(current_user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(current_user)


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление профиля текущего пользователя",
)
def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    updated = service.update_profile(
        user=current_user,
        username=data.username,
        daily_goal=data.daily_goal,
        notifications=data.notifications,
        language=data.language,
        goal=data.goal,
    )
    return UserProfileResponse.model_validate(updated)


@router.post(
    "/profile/language",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Смена изучаемого языка",
)
def update_language(
    data: LanguageUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    updated = service.update_profile(user=current_user, language=data.language)
    return UserProfileResponse.model_validate(updated)


@router.post(
    "/profile/goal",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Смена цели обучения",
)
def update_goal(
    data: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    updated = service.update_profile(user=current_user, goal=data.goal)
    return UserProfileResponse.model_validate(updated)


@router.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение общей статистики и прогресса",
)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LearningService(db)
    return service.get_stats(current_user)
