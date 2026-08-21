"""Local Memory Manager using SQLite."""
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
import logging
from contextlib import contextmanager
from config.settings import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages short-term conversation context and persistent user-specific memories/facts."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.memory_db_path
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing a managed SQLite connection that closes upon exit."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create necessary memory tables if they do not exist."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL DEFAULT 'general',
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)")
            conn.commit()

    def remember_fact(self, key: str, value: str, category: str = "general") -> bool:
        """Save or update a specific fact or user preference."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (category, key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = excluded.updated_at
            """, (category.strip().lower(), key.strip().lower(), value.strip(), now, now))
            conn.commit()
            return True

    def recall_fact(self, key: str) -> Optional[str]:
        """Retrieve a stored fact by exact key match."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memories WHERE key = ?", (key.strip().lower(),))
            row = cursor.fetchone()
            return row["value"] if row else None

    def forget_fact(self, key: str) -> bool:
        """Remove a stored fact."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE key = ?", (key.strip().lower(),))
            conn.commit()
            return cursor.rowcount > 0

    def list_memories(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List stored user memories."""
        with self._connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT id, category, key, value, created_at, updated_at FROM memories WHERE category = ? ORDER BY updated_at DESC LIMIT ?",
                    (category.strip().lower(), limit)
                )
            else:
                cursor.execute(
                    "SELECT id, category, key, value, created_at, updated_at FROM memories ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories by keyword match across terms in query."""
        terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
        if not terms:
            terms = [query.strip().lower()]

        conditions = []
        params = []
        for term in terms:
            conditions.append("(key LIKE ? OR value LIKE ?)")
            p = f"%{term}%"
            params.extend([p, p])

        where_clause = " OR ".join(conditions)
        sql = f"SELECT id, category, key, value, created_at, updated_at FROM memories WHERE {where_clause} ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def count_memories(self) -> int:
        """Count total persistent memories stored."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM memories")
            return cursor.fetchone()["total"]

    def save_message(self, role: str, content: str, session_id: str = "default") -> None:
        """Save a message to short-term conversation history."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, now))
            conn.commit()

    def get_recent_history(self, limit: int = 6, session_id: str = "default") -> List[Dict[str, str]]:
        """Retrieve recent conversation turns in chronological order."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM (
                    SELECT id, role, content, timestamp
                    FROM conversations
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                ) ORDER BY id ASC
            """, (session_id, limit))
            return [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]

    def clear_history(self, session_id: Optional[str] = None) -> None:
        """Clear conversation history."""
        with self._connection() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            else:
                cursor.execute("DELETE FROM conversations")
            conn.commit()
