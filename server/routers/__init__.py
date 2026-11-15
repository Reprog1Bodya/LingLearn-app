from server.routers.auth import router as auth_router
from server.routers.users import router as users_router
from server.routers.dictionaries import router as dictionaries_router
from server.routers.words import router as words_router
from server.routers.learning import router as learning_router
from server.routers.languages import router as languages_router
from server.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "users_router",
    "dictionaries_router",
    "words_router",
    "learning_router",
    "languages_router",
    "admin_router",
]
