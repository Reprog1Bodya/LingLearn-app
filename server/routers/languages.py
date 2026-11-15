from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from server.database.connection import get_db
from server.schemas.language import LanguageResponse, LanguageFeatureResponse, GoalResponse
from server.repositories.language_repository import LanguageRepository

router = APIRouter(tags=["Languages & Features"])

# Системные цели изучения языка
GOALS = [
    {"code": "travel", "name": "Путешествия", "descr": "Аэропорт, отель, кафе, навигация в городе"},
    {"code": "business", "name": "Бизнес и карьера", "descr": "Переговоры, контракты, деловая переписка"},
    {"code": "study", "name": "Учёба и наука", "descr": "Лекции, экзамены, терминология, академическое чтение"},
    {"code": "it", "name": "IT и разработка", "descr": "Программирование, архитектура, код-ревью, спринты"},
]


@router.get(
    "/languages",
    status_code=status.HTTP_200_OK,
    summary="Список поддерживаемых языков",
)
def list_languages(db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    items = repo.list_all()
    return {"items": [LanguageResponse.model_validate(it) for it in items]}


@router.get(
    "/goals",
    status_code=status.HTTP_200_OK,
    summary="Список доступных целей изучения языка",
)
def list_goals():
    return {"items": [GoalResponse(**g) for g in GOALS]}


@router.get(
    "/features",
    status_code=status.HTTP_200_OK,
    summary="Особенности и правила выбранного языка",
)
def list_features(
    lang: str = Query(..., description="Код языка (например en, de, fi)"),
    db: Session = Depends(get_db),
):
    repo = LanguageRepository(db)
    items = repo.list_features(lang)
    return {"items": [LanguageFeatureResponse.model_validate(it) for it in items]}
