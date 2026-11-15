from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from server.database.connection import get_db
from server.models.user import User
from server.schemas.learning import (
    TestGenerateResponse,
    TestResultSubmitRequest,
    TestResultResponse,
)
from server.services.auth_service import get_current_user
from server.services.learning_service import LearningService

router = APIRouter(tags=["Learning & Tests"])


@router.get(
    "/test",
    response_model=TestGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Генерация тренировочного теста для словаря",
)
def get_test(
    dict_id: int = Query(..., description="ID словаря для тестирования"),
    kind: str = Query(default="translate", description="translate, cards, listening, spelling"),
    n: int = Query(default=8, ge=2, le=30, description="Количество вопросов"),
    db: Session = Depends(get_db),
):
    service = LearningService(db)
    return service.generate_test(dict_id=dict_id, kind=kind, count=n)


@router.post(
    "/test/result",
    response_model=TestResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Сохранение результатов прохождения теста",
)
def save_test_result(
    data: TestResultSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LearningService(db)
    return service.submit_test_result(
        current_user=current_user,
        dict_id=data.dict_id,
        kind=data.kind,
        score=data.score,
        total=data.total,
        answers=data.answers,
    )
