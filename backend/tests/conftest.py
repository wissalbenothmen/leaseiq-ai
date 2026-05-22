import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-minimum-32-chars-ok!")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
# Force the Whisper service into mock mode for offline-safe tests.
os.environ["MOCK_WHISPER"] = "true"
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database import Base, get_db
from app.main import app
from app.auth import hash_password, create_access_token
from app.models.user import User
from app.models.lease import CommercialLease
from datetime import date

# Monkey-patch bcrypt to avoid bcrypt version compatibility issues
try:
    import bcrypt
    if not hasattr(bcrypt, '__about__'):
        bcrypt.__about__ = type('about', (), {'__version__': '4.0.0'})()
except Exception:
    pass

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    AsyncSession_ = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with AsyncSession_() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine):
    AsyncSession_ = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with AsyncSession_() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(engine):
    """Authenticated AsyncClient — registers + logs in a fresh user per test."""
    AsyncSession_ = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with AsyncSession_() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        unique = uuid.uuid4().hex[:8]
        email = f"test_{unique}@example.com"
        reg = await c.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "TestPass1!", "full_name": "Test User"},
        )
        assert reg.status_code == 201, f"Registration failed: {reg.text}"
        login = await c.post(
            "/api/v1/auth/login",
            json={"username": email, "password": "TestPass1!"},
        )
        assert login.status_code == 200, f"Login failed: {login.text}"
        token = login.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_lease(db_session):
    """Create a sample lease for testing."""
    lease = CommercialLease(
        property_address="123 Main St, New York, NY",
        tenant_name="Acme Corp",
        landlord_name="Landlord LLC",
        lease_type="gross",
        term_start=date(2020, 1, 1),
        term_end=date(2025, 12, 31),
        base_rent=5000.00,
        rent_escalation_pct=3.0,
        status="active",
        suite_number="100",
        square_footage=5000.0,
    )
    db_session.add(lease)
    await db_session.commit()
    await db_session.refresh(lease)
    return lease
