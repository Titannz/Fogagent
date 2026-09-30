"""Isolated and deterministic local Python code runner with timeout and human gate."""
import sys
import subprocess
import tempfile
from pathlib import Path
from tools.base_tool import BaseTool, ToolResult, RiskLevel


class PythonRunnerTool(BaseTool):
    """Executes deterministic Python scripts in a separate process with a strict timeout."""

    name = "python_runner"
    description = "Chạy đoạn mã Python cục bộ trong môi trường tiến trình con có giới hạn thời gian (Timeout)."
    risk_level = RiskLevel.HIGH
    parameters = {
        "code": {
            "type": "string",
            "description": "Đoạn mã Python cần chạy (in kết quả qua print)."
        },
        "timeout": {
            "type": "integer",
            "description": "Thời gian chạy tối đa tính bằng giây (mặc định: 5s, tối đa: 15s)."
        }
    }

    def __init__(self, python_executable: str = sys.executable):
        self.python_executable = python_executable

    def run(self, code: str, timeout: int = 5, **kwargs) -> ToolResult:
        if not code or not code.strip():
            return ToolResult(success=False, output="", error="Mã nguồn không được để trống.")

        bounded_timeout = min(max(1, timeout), 15)

        # Write code to a temporary file
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_path = Path(temp_file.name)

        try:
            process = subprocess.run(
                [self.python_executable, str(temp_path)],
                capture_output=True,
                text=True,
                timeout=bounded_timeout,
                encoding="utf-8",
                errors="replace"
            )

            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            if process.returncode != 0:
                err_msg = stderr if stderr else f"Tiến trình kết thúc với mã lỗi {process.returncode}"
                return ToolResult(
                    success=False,
                    output=stdout,
                    error=f"Lỗi thực thi Python:\n{err_msg}",
                    metadata={"exit_code": process.returncode}
                )

            output = stdout if stdout else "(Mã lệnh đã chạy thành công nhưng không có kết quả in ra màn hình)"
            return ToolResult(
                success=True,
                output=output,
                metadata={"exit_code": 0, "has_stderr": bool(stderr)}
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Tác vụ bị hủy vì vượt quá giới hạn thời gian chạy ({bounded_timeout}s)."
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Lỗi hệ thống khi khởi chạy tiến trình: {str(e)}")
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass
