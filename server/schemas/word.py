from pydantic import BaseModel, Field, ConfigDict


class WordCreateRequest(BaseModel):
    dict_id: int | None = None
    word: str = Field(min_length=1, max_length=128)
    translation: str = Field(min_length=1, max_length=256)
    transcription: str = Field(default="", max_length=128)
    example: str = Field(default="", max_length=500)


class WordUpdateRequest(BaseModel):
    word: str | None = Field(default=None, min_length=1, max_length=128)
    translation: str | None = Field(default=None, min_length=1, max_length=256)
    transcription: str | None = Field(default=None, max_length=128)
    example: str | None = Field(default=None, max_length=500)


class WordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dict_id: int
    word: str
    translation: str
    transcription: str = ""
    example: str = ""
    learned: int = 0


class WordLearnedRequest(BaseModel):
    learned: bool


class WordListResponse(BaseModel):
    items: list[WordResponse]
    total: int = 0
    limit: int = 20
    offset: int = 0
