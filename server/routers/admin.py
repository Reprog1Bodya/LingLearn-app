from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from server.database.connection import get_db
from server.models.user import User
from server.schemas.admin import AdminAnalyticsResponse
from server.schemas.user import UserPublicResponse
from server.schemas.dictionary import DictionaryCreateRequest, DictionaryResponse
from server.schemas.word import WordCreateRequest, WordResponse
from server.schemas.common import MessageResponse
from server.services.auth_service import get_current_admin
from server.services.admin_service import AdminService
from server.services.dictionary_service import DictionaryService
from server.services.word_service import WordService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get(
    "/analytics",
    response_model=AdminAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Аналитика платформы (только admin)",
)
def get_analytics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_analytics()


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    summary="Список зарегистрированных пользователей (только admin)",
)
def list_users(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    users = service.list_users(limit=limit, offset=offset)
    return {"items": [UserPublicResponse.model_validate(u) for u in users]}


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Удаление пользователя (только admin)",
)
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    service.delete_user(target_user_id=user_id, current_admin=admin)
    return MessageResponse(message="Пользователь успешно удалён")


@router.post(
    "/dictionaries",
    response_model=DictionaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание системного словаря (только admin)",
)
def admin_create_dictionary(
    data: DictionaryCreateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    d = service.create_dictionary(
        current_user=admin,
        lang=data.lang,
        goal=data.goal,
        title=data.title,
        description=data.description,
        is_public=True,
    )
    return DictionaryResponse(
        id=d.id,
        lang=d.lang,
        goal=d.goal,
        title=d.title,
        descr=d.description,
        cnt=0,
        author_id=d.author_id,
    )


@router.post(
    "/admin/words",
    response_model=WordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление слова в системный словарь (только admin)",
)
def admin_create_word(
    data: WordCreateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    w = service.create_word(
        current_user=admin,
        dict_id=data.dict_id,
        word=data.word,
        translation=data.translation,
        transcription=data.transcription,
        example=data.example,
    )
    return WordResponse(
        id=w.id,
        dict_id=w.dict_id,
        word=w.word,
        translation=w.translation,
        transcription=w.transcription,
        example=w.example,
    )
