from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session

from server.database.connection import get_db
from server.models.user import User
from server.schemas.dictionary import (
    DictionaryCreateRequest,
    DictionaryUpdateRequest,
    DictionaryResponse,
    DictionaryListResponse,
)
from server.schemas.word import WordListResponse
from server.schemas.common import MessageResponse
from server.services.auth_service import get_current_user
from server.services.dictionary_service import DictionaryService
from server.services.word_service import WordService

router = APIRouter(tags=["Dictionaries"])


@router.get(
    "/dictionaries",
    response_model=DictionaryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список словарей с серверным поиском и фильтрацией",
)
def list_dictionaries(
    lang: str | None = None,
    goal: str | None = None,
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    items = service.list_dictionaries(
        current_user=current_user,
        lang=lang,
        goal=goal,
        search=search,
        limit=limit,
        offset=offset,
    )
    return DictionaryListResponse(items=items, total=len(items))


@router.get(
    "/dictionaries/{dict_id}",
    response_model=DictionaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение словаря по ID",
)
def get_dictionary(
    dict_id: int,
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    d = service.get_by_id(dict_id)
    return DictionaryResponse(
        id=d.id,
        lang=d.lang,
        goal=d.goal,
        title=d.title,
        descr=d.description,
        cnt=len(d.words),
        author_id=d.author_id,
    )


@router.post(
    "/dictionaries",
    response_model=DictionaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового словаря",
)
def create_dictionary(
    data: DictionaryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    d = service.create_dictionary(
        current_user=current_user,
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


@router.put(
    "/dictionaries/{dict_id}",
    response_model=DictionaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Редактирование словаря (только автор или админ)",
)
def update_dictionary(
    dict_id: int,
    data: DictionaryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    d = service.update_dictionary(
        dict_id=dict_id,
        current_user=current_user,
        title=data.title,
        description=data.description,
        is_public=data.is_public,
    )
    return DictionaryResponse(
        id=d.id,
        lang=d.lang,
        goal=d.goal,
        title=d.title,
        descr=d.description,
        cnt=len(d.words),
        author_id=d.author_id,
    )


@router.delete(
    "/dictionaries/{dict_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление словаря (только автор или админ)",
)
def delete_dictionary(
    dict_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    service.delete_dictionary(dict_id=dict_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/dictionaries/{dict_id}/add",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Добавление словаря в список изучаемых",
)
def add_to_my_dictionaries(
    dict_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    service.toggle_user_dictionary(user_id=current_user.id, dict_id=dict_id, add=True)
    return MessageResponse(message="Словарь добавлен в ваши коллекции")


@router.delete(
    "/dictionaries/{dict_id}/add",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Удаление словаря из списка изучаемых",
)
def remove_from_my_dictionaries(
    dict_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = DictionaryService(db)
    service.toggle_user_dictionary(user_id=current_user.id, dict_id=dict_id, add=False)
    return MessageResponse(message="Словарь убран из ваших коллекций")


@router.get(
    "/dictionaries/{dict_id}/words",
    response_model=WordListResponse,
    status_code=status.HTTP_200_OK,
    summary="Слова словаря с серверным поиском, сортировкой и пагинацией",
)
def list_words_in_dictionary(
    dict_id: int,
    search: str | None = None,
    sort_by: str = Query(default="id", pattern="^(id|word|translation|created_at)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = WordService(db)
    items, total = service.list_dictionary_words(
        dict_id=dict_id,
        search=search,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return WordListResponse(items=items, total=total, limit=limit, offset=offset)
