from pydantic import BaseModel, ConfigDict


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    native: str
    niche: int
    flag: str


class LanguageFeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str


class GoalResponse(BaseModel):
    code: str
    name: str
    descr: str
