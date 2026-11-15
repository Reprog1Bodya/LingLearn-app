from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    word_id: int
    word: str
    transcription: str = ""
    answer: str
    example: str = ""
    options: list[str] = Field(default_factory=list)


class TestGenerateResponse(BaseModel):
    kind: str
    questions: list[QuestionResponse]


class TestResultSubmitRequest(BaseModel):
    dict_id: int | None = None
    kind: str = "translate"
    score: int = Field(default=0, ge=0)
    total: int = Field(default=0, ge=0)
    answers: dict[str, bool] = Field(default_factory=dict)


class TestResultResponse(BaseModel):
    points: int
    streak: int


class TestHistoryItem(BaseModel):
    id: int
    kind: str
    score: int
    total: int
    created: int


class StatsResponse(BaseModel):
    words: int
    learned: int
    streak: int
    points: int
    tests: int
    questions: int
    correct: int
    history: list[TestHistoryItem] = Field(default_factory=list)
