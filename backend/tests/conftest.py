"""Pytest configuration for database tests."""

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from backend.database.client import close_database


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file for all tests."""
    load_dotenv()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_database_client():
    """Reset database client between tests to avoid event loop issues."""
    yield
    # Close database connection after each test
    await close_database()
