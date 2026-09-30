"""Safe local file inspector strictly jailed to the FogAgent workspace."""
from pathlib import Path
from typing import Optional
from tools.base_tool import BaseTool, ToolResult, RiskLevel
from config.settings import settings


class FileInspectorTool(BaseTool):
    """Safely inspects local files within the allowed FogAgent workspace."""

    name = "file_inspector"
    description = "Kiểm tra và đọc nội dung tệp tin trong thư mục FogAgent (bảo vệ chống Path Traversal)."
    risk_level = RiskLevel.MEDIUM
    parameters = {
        "action": {
            "type": "string",
            "description": "Hành động: 'list' (xem danh sách file) hoặc 'read' (đọc nội dung file)."
        },
        "path": {
            "type": "string",
            "description": "Đường dẫn tương đối từ gốc FogAgent (ví dụ: 'data/docs', 'config/settings.py')."
        },
        "max_lines": {
            "type": "integer",
            "description": "Số dòng tối đa cần đọc (mặc định: 100 dòng)."
        }
    }

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or settings.base_dir).resolve()

    def _resolve_safe_path(self, user_path: str) -> Path:
        """Resolve path and ensure it does not escape the workspace root."""
        clean_path = user_path.strip().lstrip("/\\")
        target = (self.workspace_root / clean_path).resolve()
        # Path traversal guard
        if not str(target).startswith(str(self.workspace_root)):
            raise PermissionError(f"Truy cập ngoài thư mục cho phép bị chặn: {user_path}")
        return target

    def run(self, action: str, path: str = ".", max_lines: int = 100, **kwargs) -> ToolResult:
        try:
            target_path = self._resolve_safe_path(path)
        except PermissionError as pe:
            return ToolResult(success=False, output="", error=str(pe))

        if not target_path.exists():
            return ToolResult(success=False, output="", error=f"Đường dẫn không tồn tại: {path}")

        action = action.lower().strip()

        if action == "list":
            if not target_path.is_dir():
                return ToolResult(success=False, output="", error=f"'{path}' không phải là một thư mục.")

            items = []
            for child in sorted(target_path.iterdir()):
                prefix = "[DIR] " if child.is_dir() else "[FILE]"
                size_str = f"({child.stat().st_size} bytes)" if child.is_file() else ""
                items.append(f"{prefix} {child.name} {size_str}")

            output = "\n".join(items) if items else "(Thư mục trống)"
            return ToolResult(success=True, output=output, metadata={"path": str(target_path), "count": len(items)})

        elif action == "read":
            if not target_path.is_file():
                return ToolResult(success=False, output="", error=f"'{path}' không phải là tệp tin.")

            # Do not read binary files
            if target_path.suffix.lower() in (".pdf", ".db", ".sqlite", ".exe", ".bin", ".pyc"):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Tệp nhị phân ({target_path.suffix}) không thể đọc dạng văn bản thô."
                )

            try:
                lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines()
                preview = lines[:max_lines]
                numbered = [f"{i+1:4d} | {line}" for i, line in enumerate(preview)]
                output = "\n".join(numbered)
                if len(lines) > max_lines:
                    output += f"\n... (còn {len(lines) - max_lines} dòng chưa hiển thị)"
                return ToolResult(success=True, output=output, metadata={"total_lines": len(lines)})
            except Exception as e:
                return ToolResult(success=False, output="", error=f"Lỗi đọc tệp: {str(e)}")

        else:
            return ToolResult(success=False, output="", error=f"Hành động '{action}' không hợp lệ (chỉ hỗ trợ 'list' hoặc 'read').")
