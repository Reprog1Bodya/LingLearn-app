from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session

from server.database.connection import get_db
from server.models.user import User
from server.schemas.word import (
    WordCreateRequest,
    WordUpdateRequest,
    WordResponse,
    WordListResponse,
    WordLearnedRequest,
)
from server.schemas.common import MessageResponse
from server.services.auth_service import get_current_user
from server.services.word_service import WordService

router = APIRouter(tags=["Words"])


@router.get(
    "/my/words",
    response_model=WordListResponse,
    status_code=status.HTTP_200_OK,
    summary="Слова пользователя с серверным поиском, фильтрацией, сортировкой и пагинацией",
)
def list_my_words(
    filter: str | None = Query(default=None, description="all, learned, unlearned"),
    search: str | None = Query(default=None, description="Поиск по слову или переводу"),
    sort_by: str = Query(default="id", pattern="^(id|word|translation|created_at)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    items, total = service.list_my_words(
        user_id=current_user.id,
        filter_type=filter,
        search=search,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return WordListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/my/words",
    response_model=WordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание слова в словаре пользователя",
)
@router.post(
    "/words",
    response_model=WordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание слова в словаре пользователя (алиас)",
    include_in_schema=False,
)
def create_word(
    data: WordCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    w = service.create_word(
        current_user=current_user,
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
        learned=0,
    )


@router.get(
    "/my/words/{word_id}",
    response_model=WordResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение слова по ID",
)
@router.get(
    "/words/{word_id}",
    response_model=WordResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение слова по ID (алиас)",
    include_in_schema=False,
)
def get_word(
    word_id: int,
    db: Session = Depends(get_db),
):
    service = WordService(db)
    w = service.get_by_id(word_id)
    return WordResponse(
        id=w.id,
        dict_id=w.dict_id,
        word=w.word,
        translation=w.translation,
        transcription=w.transcription,
        example=w.example,
    )


@router.put(
    "/my/words/{word_id}",
    response_model=WordResponse,
    status_code=status.HTTP_200_OK,
    summary="Редактирование слова (CRUD, проверка владельца)",
)
@router.put(
    "/words/{word_id}",
    response_model=WordResponse,
    status_code=status.HTTP_200_OK,
    summary="Редактирование слова (алиас)",
    include_in_schema=False,
)
def update_word(
    word_id: int,
    data: WordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    w = service.update_word(
        word_id=word_id,
        current_user=current_user,
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


@router.delete(
    "/my/words/{word_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление слова (CRUD, проверка владельца)",
)
@router.delete(
    "/words/{word_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление слова (алиас)",
    include_in_schema=False,
)
def delete_word(
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    service.delete_word(word_id=word_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/words/{word_id}/learned",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Переключение отметки «выучено» для слова",
)
def toggle_word_learned(
    word_id: int,
    data: WordLearnedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    service.set_learned(word_id=word_id, user_id=current_user.id, learned=data.learned)
    return MessageResponse(message="Статус изучения обновлён")
