"""MongoDB database client for async operations."""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from backend.database.exceptions import DatabaseConnectionError


# Global client and database instances
_client = None
_database = None


async def get_database():
    """Get MongoDB database instance.

    Returns:
        AsyncIOMotorDatabase: The folder_magic database

    Raises:
        DatabaseConnectionError: If MONGODB_URI is not set
    """
    global _client, _database
    if _database is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise DatabaseConnectionError("MONGODB_URI environment variable not set")
        _client = AsyncIOMotorClient(uri)
        _database = _client["folder_magic"]
    return _database


async def close_database():
    """Close MongoDB connection."""
    global _client, _database
    if _client:
        _client.close()
        _client = None
        _database = None
