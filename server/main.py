import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.database.config import settings
from server.database.connection import SessionLocal
from server.database.migrate import upgrade_head
from server.database.seed_data import seed_database
from server.routers import (
    auth_router,
    users_router,
    dictionaries_router,
    words_router,
    learning_router,
    languages_router,
    admin_router,
)

# Настройка серверного логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("linglearn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: инициализация БД и наполнение данными."""
    # Схема БД создаётся ТОЛЬКО миграциями Alembic (никакого create_all на старте)
    if settings.AUTO_MIGRATE:
        upgrade_head()

    if settings.SEED_ON_STARTUP:
        logger.info("Проверка и заполнение начальными данными (seed)...")
        with SessionLocal() as db:
            nd, nw = seed_database(db)
            if nd or nw:
                logger.info(f"Загружено начальных данных: новых словарей: {nd}, новых слов: {nw}")

    logger.info(f"Сервер LingLearn успешно запущен на http://{settings.HOST}:{settings.PORT}")
    yield
    logger.info("Остановка сервера LingLearn...")


app = FastAPI(
    title="LingLearn API",
    version="1.0.0",
    description="REST API для мобильного приложения по изучению иностранных языков LingLearn",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Безопасная обработка исключений (без раскрытия внутренних деталей сервера)
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Преобразуем ошибки валидации Pydantic в понятный читаемый формат
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Некорректное значение")
        errors.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "; ".join(errors)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Внутренние исключения логируются на сервере, но клиенту отдается безопасное сообщение
    logger.error(f"Необработанная ошибка сервера при запросе {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера. Пожалуйста, обратитесь к администратору."},
    )


# ============================================================================
# Маршрутизация (с версионированием /api/v1 и совместимостью с корнем)
# ============================================================================

# Проверка работоспособности
@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}


# Подключение версионированных роутеров /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(dictionaries_router, prefix="/api/v1")
app.include_router(words_router, prefix="/api/v1")
app.include_router(learning_router, prefix="/api/v1")
app.include_router(languages_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# Совместимость с корневыми путями для клиентов
app.include_router(auth_router, include_in_schema=False)
app.include_router(users_router, include_in_schema=False)
app.include_router(dictionaries_router, include_in_schema=False)
app.include_router(words_router, include_in_schema=False)
app.include_router(learning_router, include_in_schema=False)
app.include_router(languages_router, include_in_schema=False)
app.include_router(admin_router, include_in_schema=False)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
