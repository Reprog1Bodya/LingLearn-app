from server.schemas.common import MessageResponse, DetailResponse, PaginationParams, PaginatedResponse
from server.schemas.user import UserProfileResponse, UserUpdateRequest, UserPublicResponse
from server.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    PasswordRecoverRequest,
    PasswordRecoverResponse,
    PasswordRecoverConfirmRequest,
)
from server.schemas.dictionary import (
    DictionaryCreateRequest,
    DictionaryUpdateRequest,
    DictionaryResponse,
    DictionaryListResponse,
)
from server.schemas.word import (
    WordCreateRequest,
    WordUpdateRequest,
    WordResponse,
    WordLearnedRequest,
    WordListResponse,
)
from server.schemas.learning import (
    QuestionResponse,
    TestGenerateResponse,
    TestResultSubmitRequest,
    TestResultResponse,
    TestHistoryItem,
    StatsResponse,
)
from server.schemas.language import LanguageResponse, LanguageFeatureResponse, GoalResponse
from server.schemas.admin import AdminAnalyticsResponse

__all__ = [
    "MessageResponse",
    "DetailResponse",
    "PaginationParams",
    "PaginatedResponse",
    "UserProfileResponse",
    "UserUpdateRequest",
    "UserPublicResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "PasswordRecoverRequest",
    "PasswordRecoverResponse",
    "PasswordRecoverConfirmRequest",
    "DictionaryCreateRequest",
    "DictionaryUpdateRequest",
    "DictionaryResponse",
    "DictionaryListResponse",
    "WordCreateRequest",
    "WordUpdateRequest",
    "WordResponse",
    "WordLearnedRequest",
    "WordListResponse",
    "QuestionResponse",
    "TestGenerateResponse",
    "TestResultSubmitRequest",
    "TestResultResponse",
    "TestHistoryItem",
    "StatsResponse",
    "LanguageResponse",
    "LanguageFeatureResponse",
    "GoalResponse",
    "AdminAnalyticsResponse",
]
