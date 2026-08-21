"""Local Knowledge Manager using SQLite."""
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
import logging
from contextlib import contextmanager
from config.settings import settings

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Stores and retrieves evaluated, structured general knowledge."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.knowledge_db_path
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
        """Initialize the knowledge database schema."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'user_study',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    tags TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON knowledge(topic)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge(tags)")
            conn.commit()

    def add_knowledge(
        self,
        topic: str,
        content: str,
        source: str = "user_study",
        confidence: float = 1.0,
        tags: Optional[List[str]] = None
    ) -> int:
        """Add a structured knowledge record."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tag_str = ",".join([t.strip().lower() for t in tags]) if tags else ""

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge (topic, content, source, confidence, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (topic.strip(), content.strip(), source.strip(), confidence, tag_str, now, now))
            conn.commit()
            return cursor.lastrowid

    def get_by_id(self, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a knowledge entry by ID."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge WHERE id = ?", (knowledge_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Retrieve knowledge entries by exact or partial topic match."""
        pattern = f"%{topic.strip().lower()}%"
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM knowledge
                WHERE LOWER(topic) LIKE ?
                ORDER BY updated_at DESC
            """, (pattern,))
            return [dict(row) for row in cursor.fetchall()]

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge across topic, content, and tags."""
        terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
        if not terms:
            terms = [query.strip().lower()]

        conditions = []
        params = []
        for term in terms:
            conditions.append("(LOWER(topic) LIKE ? OR LOWER(content) LIKE ? OR LOWER(tags) LIKE ?)")
            p = f"%{term}%"
            params.extend([p, p, p])

        where_clause = " OR ".join(conditions)
        sql = f"SELECT * FROM knowledge WHERE {where_clause} ORDER BY confidence DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all stored knowledge records."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_knowledge(self, knowledge_id: int) -> bool:
        """Delete a knowledge record by ID."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge WHERE id = ?", (knowledge_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count_knowledge(self) -> int:
        """Count total knowledge records."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM knowledge")
            return cursor.fetchone()["total"]
