"""Base class and common types for Secure Local Tools in FogAgent."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import time


class RiskLevel(str, Enum):
    """Risk classification for deterministic local tools."""
    LOW = "LOW"        # Pure mathematical calculation, stateless read-only queries
    MEDIUM = "MEDIUM"  # Local file reading, database structure inspection
    HIGH = "HIGH"      # Python script execution, state modifications


@dataclass
class ToolResult:
    """Standardized result returned by all deterministic local tools."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": round(self.execution_time, 4),
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """Abstract base class for all deterministic local tools."""

    name: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """Execute the deterministic tool logic. Subclasses must implement."""
        pass

    def execute(self, **kwargs) -> ToolResult:
        """Execute with execution time tracking and exception handling."""
        start_time = time.time()
        try:
            result = self.run(**kwargs)
            result.execution_time = time.time() - start_time
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{self.name}' execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def format_call_summary(self, **kwargs) -> str:
        """Format a human-readable summary of the tool invocation for verification."""
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        return f"{self.name}({params_str})"
