import asyncio
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.api.models import metadata
from src.config import (
    DB_HOST_TEST,
    DB_NAME_TEST,
    DB_PASS_TEST,
    DB_PORT_TEST,
    DB_USER_TEST,
)
from src.database import get_async_session
from src.main import app

__all__ = ["ac", "event_loop", "override_async_session", "prepare_database"]


DATABASE_URL_TEST = (
    f"postgresql+asyncpg://"
    f"{DB_USER_TEST}:{DB_PASS_TEST}@"
    f"{DB_HOST_TEST}:{DB_PORT_TEST}/{DB_NAME_TEST}"
)

engine_test = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
async_session_maker = async_sessionmaker(engine_test, expire_on_commit=False)
metadata.bind = engine_test


async def override_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


app.dependency_overrides[get_async_session] = override_async_session


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(metadata.create_all)

    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
