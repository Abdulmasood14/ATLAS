"""
Database Connection Management

Provides connection pooling and async database operations for the chatbot.
"""
import os
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool


class DatabaseManager:
    """
    Database connection manager with connection pooling
    """

    def __init__(
        self,
        host: str = "localhost",
        database: str = "financial_rag",
        user: str = "postgres",
        password: str = "Prasanna!@#2002",
        min_connections: int = 2,
        max_connections: int = 10
    ):
        """
        Initialize database manager

        Args:
            host: PostgreSQL host
            database: Database name
            user: Database user
            password: Database password
            min_connections: Minimum pool connections
            max_connections: Maximum pool connections
        """
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password
        }

        # Create connection pool
        self.pool = SimpleConnectionPool(
            min_connections,
            max_connections,
            **self.connection_params
        )

    def get_connection(self):
        """
        Get a connection from the pool

        Returns:
            psycopg2 connection
        """
        return self.pool.getconn()

    def return_connection(self, conn):
        """
        Return connection to the pool

        Args:
            conn: Connection to return
        """
        self.pool.putconn(conn)

    @asynccontextmanager
    async def get_cursor(self, dict_cursor: bool = True):
        """
        Context manager for getting a database cursor

        Args:
            dict_cursor: Use RealDictCursor (returns rows as dicts)

        Yields:
            Database cursor
        """
        conn = self.get_connection()
        try:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)

    def close_all_connections(self):
        """Close all connections in the pool"""
        self.pool.closeall()


# ============================================================================
# Singleton instance
# ============================================================================

_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create singleton database manager

    Returns:
        DatabaseManager instance
    """
    global _db_manager

    if _db_manager is None:
        # Read from environment variables or use defaults
        _db_manager = DatabaseManager(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "financial_rag"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Prasanna!@#2002")
        )

    return _db_manager


def close_db_manager():
    """Close the database manager singleton"""
    global _db_manager

    if _db_manager is not None:
        _db_manager.close_all_connections()
        _db_manager = None


# ============================================================================
# FastAPI Dependency
# ============================================================================

async def get_db() -> AsyncGenerator[DatabaseManager, None]:
    """
    FastAPI dependency for database access

    Yields:
        DatabaseManager instance
    """
    db = get_db_manager()
    try:
        yield db
    finally:
        pass  # Connection is returned to pool automatically
