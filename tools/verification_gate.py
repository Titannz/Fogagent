import sys
from typing import Dict, Any, Callable, Optional
from tools.base_tool import BaseTool, RiskLevel


def _safe_print(text: str) -> None:
    """Print text safely across different terminal encodings."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "ascii"
        safe_text = text.encode(encoding, errors="replace").decode(encoding)
        print(safe_text)


class HumanVerificationGate:
    """Enforces explicit human approval before executing deterministic local tools."""

    def __init__(
        self,
        interactive: bool = True,
        auto_approve_low_risk: bool = True,
        prompt_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Args:
            interactive: If True, ask user for confirmation via console/callback.
            auto_approve_low_risk: If True, LOW risk tools (e.g. pure math) execute without prompt.
            prompt_callback: Optional custom input callback (e.g. for testing or UI).
        """
        self.interactive = interactive
        self.auto_approve_low_risk = auto_approve_low_risk
        self.prompt_callback = prompt_callback or input

    def verify(
        self,
        tool: BaseTool,
        kwargs: Dict[str, Any],
        purpose: str = "Tác vụ tự động từ người dùng"
    ) -> bool:
        """Verify whether tool execution is permitted by the human operator."""
        # Non-interactive mode (e.g. unit tests or automated tests)
        if not self.interactive:
            return True

        # Safe low-risk bypass if enabled
        if self.auto_approve_low_risk and tool.risk_level == RiskLevel.LOW:
            return True

        # Render verification dialog
        risk_icon = "[!]" if tool.risk_level == RiskLevel.MEDIUM else "[ALERT]"
        _safe_print("\n+-- [XAC THUC CONG CU CUC BO / TOOL GATE] -----------------+")
        _safe_print(f"| {risk_icon} Cong cu: {tool.name}")
        _safe_print(f"| * Muc do rui ro: {tool.risk_level.value}")
        _safe_print(f"| * Lenh goi: {tool.format_call_summary(**kwargs)}")
        _safe_print(f"| * Muc dich: {purpose}")
        _safe_print("+----------------------------------------------------------+")

        try:
            choice = self.prompt_callback("Ban co cho phep thuc thi cong cu nay khong? (y/n): ").strip().lower()
            if choice == "y":
                return True
            else:
                _safe_print("[X] Da tu choi thuc thi cong cu.")
                return False
        except (KeyboardInterrupt, EOFError):
            _safe_print("\n[X] Thao tac bi gian doan.")
            return False
