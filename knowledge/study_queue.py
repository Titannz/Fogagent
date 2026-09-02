"""Deferred Study Queue Manager using SQLite."""
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
from contextlib import contextmanager
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class StudyQueue:
    """Manages deferred study materials for processing when resources/time permit."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.knowledge_dir / "study_queue.db")
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize the study queue table."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'user_request',
                    estimated_seconds INTEGER NOT NULL DEFAULT 60,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_queue_status ON study_queue(status)")
            conn.commit()

    def add_item(
        self,
        title: str,
        content: str,
        source: str = "user_request",
        estimated_seconds: int = 60
    ) -> int:
        """Add a study material to the deferred queue."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO study_queue (title, content, source, estimated_seconds, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """, (title.strip(), content.strip(), source.strip(), estimated_seconds, now, now))
            conn.commit()
            return cursor.lastrowid

    def get_pending(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve all pending items in the queue."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM study_queue
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_item(self, queue_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific queue item by ID."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_queue WHERE id = ?", (queue_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def mark_completed(self, queue_id: int) -> bool:
        """Mark a queue item as completed."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE study_queue
                SET status = 'completed', updated_at = ?
                WHERE id = ?
            """, (now, queue_id))
            conn.commit()
            return cursor.rowcount > 0

    def remove_item(self, queue_id: int) -> bool:
        """Delete an item from the study queue."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM study_queue WHERE id = ?", (queue_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count_pending(self) -> int:
        """Return the number of pending study items."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM study_queue WHERE status = 'pending'")
            return cursor.fetchone()["total"]

    def clear_all(self) -> None:
        """Clear all records from the queue."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM study_queue")
            conn.commit()
