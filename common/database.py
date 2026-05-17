from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings

# 1. Создаем асинхронный движок (DB_URL берется из конфига)
engine = create_async_engine(
    settings.DB_URL,
    echo=True,  # Включает логирование SQL-запросов (удобно при разработке)
    pool_pre_ping=True,  # Защита от «отваливания» соединений с БД в продакшне
)

# 2. Фабрика сессий - создает объект сессии, через который совершаются запросы
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 3. Функция-помощник (Dependency) - используется в FastAPI для автоматического открытия/закрытия сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
