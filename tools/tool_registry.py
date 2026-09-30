"""Central Tool Registry for registering, discovering, and securely executing local tools."""
from typing import Dict, List, Any, Optional
import json
import re
from tools.base_tool import BaseTool, ToolResult
from tools.verification_gate import HumanVerificationGate
from tools.math_evaluator import MathEvaluatorTool
from tools.file_inspector import FileInspectorTool
from tools.db_inspector import DatabaseInspectorTool
from tools.python_runner import PythonRunnerTool


class ToolRegistry:
    """Manages the lifecycle, discovery, and guarded execution of deterministic local tools."""

    def __init__(self, verification_gate: Optional[HumanVerificationGate] = None):
        self.tools: Dict[str, BaseTool] = {}
        self.verification_gate = verification_gate or HumanVerificationGate()
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the 4 core secure local tools."""
        self.register(MathEvaluatorTool())
        self.register(FileInspectorTool())
        self.register(DatabaseInspectorTool())
        self.register(PythonRunnerTool())

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return metadata summary for all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level.value,
                "parameters": t.parameters
            }
            for t in self.tools.values()
        ]

    def get_tool_prompt(self) -> str:
        """Format tools specification for system context."""
        lines = [
            "[HỆ THỐNG CÔNG CỤ CỤC BỘ / SECURE LOCAL TOOLS]:",
            "Bạn có quyền truy cập vào các công cụ nội bộ sau để tính toán và kiểm tra dữ liệu.",
            "Khi cần dùng công cụ, hãy gọi cú pháp dạng JSON duy nhất:",
            '```tool_call',
            '{"tool": "<tên_công_cụ>", "args": {<các_tham_số>}, "purpose": "<mục_đích>"}',
            '```',
            "Danh sách công cụ khả dụng:"
        ]
        for t in self.tools.values():
            params_str = json.dumps(t.parameters, ensure_ascii=False)
            lines.append(f"- `{t.name}` (Rủi ro: {t.risk_level.value}): {t.description}")
            lines.append(f"  Tham số: {params_str}")
        return "\n".join(lines)

    def execute_tool(
        self,
        name: str,
        kwargs: Dict[str, Any],
        purpose: str = "Thực thi công cụ theo yêu cầu",
        bypass_gate: bool = False
    ) -> ToolResult:
        """Securely execute a registered tool with Human Verification Gate enforcement."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Không tìm thấy công cụ '{name}'. Các công cụ hiện có: {', '.join(self.tools.keys())}"
            )

        # Enforce Human Verification Gate unless explicitly bypassed
        if not bypass_gate:
            approved = self.verification_gate.verify(tool, kwargs, purpose=purpose)
            if not approved:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Thao tác '{name}' đã bị từ chối bởi người dùng (Human Verification Gate)."
                )

        # Execute deterministic tool
        return tool.execute(**kwargs)

    @staticmethod
    def extract_tool_call(text: str) -> Optional[Dict[str, Any]]:
        """Extract a tool call JSON from text if present."""
        # Match ```tool_call ... ``` or {"tool": ..., "args": ...}
        pattern = r'```(?:tool_call|json)?\s*(\{[\s\S]*?"tool"[\s\S]*?\})\s*```'
        match = re.search(pattern, text)
        raw_json = match.group(1) if match else None

        if not raw_json:
            # Fallback search for bare JSON object with "tool" and "args"
            bare_pattern = r"(\{\s*\"tool\"\s*:\s*\"[^\"]+\"\s*,\s*\"args\"\s*:\s*\{[\s\S]*?\}\s*(?:,\s*\"purpose\"\s*:\s*\"[^\"]*\")?\s*\})"
            bare_match = re.search(bare_pattern, text)
            if bare_match:
                raw_json = bare_match.group(1)

        if raw_json:
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                    return parsed
            except Exception:
                pass
        return None
