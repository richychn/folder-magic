"""Custom exceptions for database operations."""


class DatabaseError(Exception):
    """Base database error"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Can't connect to database"""
    pass
