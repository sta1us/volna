from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Импортируем наш конфиг и роутеры
from common.config import settings
from src.routes import (
    auth,
    events,
    location,
    media,
    menu,
    reviews,
    stats,
    suggestions,
    team,
    users,
)


# --- 1. СОВРЕМЕННЫЙ LIFESPAN ДЛЯ СТАРТА ПРИЛОЖЕНИЯ ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.
    Заменяет устаревшие события @app.on_event("startup"/"shutdown").
    """
    # Вычисляем коренную директорию загрузок на основе конфига
    base_upload_dir = Path(settings.UPLOAD_DIR)

    # Динамически собираем подпапки, которые требуются модулям системы
    upload_paths = [
        base_upload_dir / "menu",
        base_upload_dir / "events",
        base_upload_dir / "event",
        base_upload_dir / "team",
        base_upload_dir / "location",
        base_upload_dir / "media",
    ]

    # Создаем директории. Так как это происходит до старта обработки запросов,
    # здесь синхронный вызов mkdir допустим, но теперь он централизован и безопасен.
    for path in upload_paths:
        path.mkdir(parents=True, exist_ok=True)

    yield  # В этой точке приложение запускается и начинает принимать запросы

    # Здесь (после yield) можно описать логику при остановке сервера (например, закрытие пулов)
    pass


# Инициализируем FastAPI с передачей lifespan
app = FastAPI(
    title="Volna API",
    description="Backend для сайта и Telegram-бота",
    version="2.0.0",
    lifespan=lifespan,
)

# --- 2. НАСТРОЙКА БЕЗОПАСНОСТИ CORS ---
# Безопасный список разрешенных доменов для продакшна.
# Добавляем локальные хосты для разработки и целевой домен из настроек.
allowed_origins = [
    "http://localhost:3000",  # Стандартный порт React
    "http://127.0.0.1:3000",
    settings.DOMAIN,  # Боевой домен из .env
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. ПОДКЛЮЧЕНИЕ СТАТИКИ ---
# Путь к папке статики берется строго из центрального конфигуратора
app.mount(
    f"/{settings.UPLOAD_DIR}",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads",
)

# --- 4. ПОДКЛЮЧЕНИЕ РОУТЕРОВ ---
app.include_router(auth.router, prefix="/api")
app.include_router(menu.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(suggestions.router, prefix="/api")
app.include_router(location.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(media.router, prefix="/api")


# --- 5. БАЗОВЫЙ ЭНДПОИНТ ПРОВЕРКИ СТАТУСА ---
@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности сервиса (Health Check)"""
    return {"status": "healthy", "version": app.version, "name": app.title}


# Если хочешь запускать через python src/main.py
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
