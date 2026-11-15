from pydantic import BaseModel


class AdminAnalyticsResponse(BaseModel):
    users: int
    dictionaries: int
    words: int
    tests: int
