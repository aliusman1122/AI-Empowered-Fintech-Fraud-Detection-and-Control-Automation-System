import pytest
import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from testcontainers.postgres import PostgresContainer
from unittest.mock import AsyncMock, patch

from backend.main import app
from backend.core.dependencies import get_db
from backend.models import Base
from backend.services.auth_service import create_access_token
from backend.schemas import UserRole

# Use session scope to speed up tests by reusing the exact same testcontainer DB
@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres

@pytest_asyncio.fixture(scope="session")
async def db_engine(postgres_container):
    db_url = postgres_container.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
    os.environ["TEST_DATABASE_URL"] = db_url
    engine = create_async_engine(db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    async with SessionLocal() as session:
        yield session
        # Rollback all uncommitted changes created by the specific test case
        await session.rollback()

@pytest_asyncio.fixture
async def async_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user():
    return {
        "id": 999,
        "email": "test@example.com",
        "role": UserRole.USER,
        "is_verified": True
    }

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user["email"], "role": test_user["role"].value})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(test_user):
    token = create_access_token(data={"sub": "admin@example.com", "role": UserRole.ADMIN.value})
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    with patch("backend.core.redis.RedisClient.ping", new_callable=AsyncMock) as mock_ping, \
         patch("backend.core.redis.RedisClient.set", new_callable=AsyncMock) as mock_set, \
         patch("backend.core.redis.RedisClient.get", new_callable=AsyncMock) as mock_get:
        mock_ping.return_value = True
        yield { "ping": mock_ping, "set": mock_set, "get": mock_get }

@pytest.fixture(autouse=True)
def mock_ml_model():
    with patch("backend.services.ml_service._model") as mock_model:
        mock_model.predict_proba.return_value = [[0.8, 0.2]]
        yield mock_model
