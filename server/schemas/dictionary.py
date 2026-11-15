from pydantic import BaseModel, Field, ConfigDict


class DictionaryCreateRequest(BaseModel):
    lang: str = Field(min_length=2, max_length=8)
    goal: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=1000)


class DictionaryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    is_public: bool | None = None


class DictionaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lang: str
    goal: str
    title: str
    descr: str = ""
    cnt: int = 0
    added: int = 0
    recommended: bool = False
    author_id: int | None = None


class DictionaryListResponse(BaseModel):
    items: list[DictionaryResponse]
    total: int = 0
