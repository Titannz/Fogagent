"""Safe and deterministic AST-based mathematical expression evaluator."""
import ast
import math
import operator
from typing import Any, Dict
from tools.base_tool import BaseTool, ToolResult, RiskLevel


class MathEvaluatorTool(BaseTool):
    """Safely evaluates mathematical expressions using AST without code execution vulnerabilities."""

    name = "math_evaluator"
    description = "Tính toán biểu thức toán học chính xác và an toàn bằng AST (không dùng eval)."
    risk_level = RiskLevel.LOW
    parameters = {
        "expression": {
            "type": "string",
            "description": "Biểu thức toán học cần tính (ví dụ: '2**10 + sqrt(144) * 5', 'factorial(6)', 'log2(1024)')"
        }
    }

    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    _ALLOWED_FUNCTIONS = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "floor": math.floor,
        "ceil": math.ceil,
        "abs": abs,
        "round": round,
        "pow": pow,
        "pi": math.pi,
        "e": math.e,
    }

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, complex)):
                return node.value
            raise ValueError(f"Giá trị kiểu '{type(node.value).__name__}' không được phép.")

        if hasattr(ast, "Num") and isinstance(node, ast.Num):  # Python compat
            return node.n

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._OPERATORS:
                raise ValueError(f"Toán tử '{op_type.__name__}' không được hỗ trợ.")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._OPERATORS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._OPERATORS:
                raise ValueError(f"Toán tử đơn '{op_type.__name__}' không được hỗ trợ.")
            operand = self._eval_node(node.operand)
            return self._OPERATORS[op_type](operand)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Chỉ được gọi các hàm toán học nằm trong danh sách cho phép.")
            func_name = node.func.id
            if func_name not in self._ALLOWED_FUNCTIONS:
                raise ValueError(f"Hàm '{func_name}' không nằm trong danh sách toán học an toàn.")
            func = self._ALLOWED_FUNCTIONS[func_name]
            args = [self._eval_node(arg) for arg in node.args]
            return func(*args)

        if isinstance(node, ast.Name):
            if node.id in self._ALLOWED_FUNCTIONS:
                val = self._ALLOWED_FUNCTIONS[node.id]
                if isinstance(val, (int, float)):
                    return val
            raise ValueError(f"Biến hoặc hàm '{node.id}' không hợp lệ.")

        raise ValueError(f"Cú pháp '{type(node).__name__}' bị từ chối vì lý do an toàn.")

    def run(self, expression: str, **kwargs) -> ToolResult:
        if not expression or not expression.strip():
            return ToolResult(success=False, output="", error="Biểu thức không được để trống.")

        clean_expr = expression.strip()
        try:
            tree = ast.parse(clean_expr, mode="eval")
            result = self._eval_node(tree)
            return ToolResult(
                success=True,
                output=str(result),
                metadata={"expression": clean_expr, "result": result}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Lỗi tính toán biểu thức '{clean_expr}': {str(e)}"
            )
