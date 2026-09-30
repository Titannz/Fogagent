"""Read-only SQLite Database Inspector for FogAgent data stores."""
import sqlite3
import re
from pathlib import Path
from typing import Dict, Any
from tools.base_tool import BaseTool, ToolResult, RiskLevel
from config.settings import settings


class DatabaseInspectorTool(BaseTool):
    """Safely inspects FogAgent local SQLite databases in strict read-only mode."""

    name = "db_inspector"
    description = "Kiểm tra cấu trúc và truy vấn chỉ đọc (SELECT) các CSDL nội bộ (knowledge.db, memory.db, study_queue.db)."
    risk_level = RiskLevel.MEDIUM
    parameters = {
        "database": {
            "type": "string",
            "description": "Tên CSDL: 'knowledge', 'memory', hoặc 'study_queue'."
        },
        "query": {
            "type": "string",
            "description": "Câu lệnh SELECT chỉ đọc hoặc để trống để xem danh sách bảng và số lượng bản ghi."
        },
        "limit": {
            "type": "integer",
            "description": "Giới hạn số dòng trả về (mặc định: 10)."
        }
    }

    _ALLOWED_DBS = {
        "knowledge": lambda: settings.knowledge_db_path,
        "memory": lambda: settings.memory_db_path,
        "study_queue": lambda: settings.knowledge_dir / "study_queue.db",
    }

    def _get_db_path(self, db_key: str) -> Path:
        key = db_key.lower().strip()
        if key not in self._ALLOWED_DBS:
            valid_keys = ", ".join(self._ALLOWED_DBS.keys())
            raise ValueError(f"CSDL '{db_key}' không hợp lệ. Chỉ chấp nhận: {valid_keys}")
        return self._ALLOWED_DBS[key]()

    def _is_safe_select(self, query: str) -> bool:
        """Ensure the query is strictly a SELECT statement and does not perform modifications."""
        clean = query.strip().upper()
        if not clean.startswith("SELECT") and not clean.startswith("PRAGMA TABLE_INFO"):
            return False
        # Block dangerous SQL keywords
        forbidden = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE",
            "TRUNCATE", "ATTACH", "DETACH", "PRAGMA WRITABLE_SCHEMA", "EXECUTE"
        ]
        tokens = re.findall(r"\b[A-Z_]+\b", clean)
        for token in tokens:
            if token in forbidden:
                return False
        return True

    def run(self, database: str, query: str = "", limit: int = 10, **kwargs) -> ToolResult:
        try:
            db_path = self._get_db_path(database)
        except ValueError as ve:
            return ToolResult(success=False, output="", error=str(ve))

        if not db_path.exists():
            return ToolResult(success=False, output="", error=f"Tệp CSDL chưa tồn tại: {db_path.name}")

        try:
            # Open SQLite in strictly read-only mode using URI
            uri_path = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri_path, uri=True)
            cursor = conn.cursor()

            # If no query provided, return table schema and counts
            if not query or not query.strip():
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = [r[0] for r in cursor.fetchall()]
                summary = [f"=== CSDL: {database} ({db_path.name}) ==="]
                for tbl in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
                    count = cursor.fetchone()[0]
                    cursor.execute(f"PRAGMA table_info({tbl});")
                    cols = [f"{c[1]} ({c[2]})" for c in cursor.fetchall()]
                    summary.append(f"• Bảng '{tbl}' ({count} bản ghi):")
                    summary.append(f"  Cột: {', '.join(cols)}")
                conn.close()
                return ToolResult(success=True, output="\n".join(summary), metadata={"tables": tables})

            # Validate custom SELECT query
            if not self._is_safe_select(query):
                conn.close()
                return ToolResult(
                    success=False,
                    output="",
                    error="Truy vấn bị từ chối: Chỉ cho phép các lệnh đọc dữ liệu SELECT an toàn."
                )

            cursor.execute(query)
            col_names = [d[0] for d in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(limit)
            conn.close()

            if not rows:
                return ToolResult(success=True, output="(Không có bản ghi phù hợp)", metadata={"count": 0})

            # Format tabular output
            header = " | ".join(col_names)
            sep = "-" * len(header)
            lines = [header, sep]
            for row in rows:
                lines.append(" | ".join(str(val) for val in row))

            return ToolResult(success=True, output="\n".join(lines), metadata={"columns": col_names, "count": len(rows)})

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Lỗi truy vấn SQLite: {str(e)}")
