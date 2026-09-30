"""Comprehensive unit tests for Secure Local Tools and Human Verification Gate."""
import unittest
import tempfile
from pathlib import Path
from tools.base_tool import RiskLevel
from tools.verification_gate import HumanVerificationGate
from tools.math_evaluator import MathEvaluatorTool
from tools.file_inspector import FileInspectorTool
from tools.db_inspector import DatabaseInspectorTool
from tools.python_runner import PythonRunnerTool
from tools.tool_registry import ToolRegistry


class TestMathEvaluator(unittest.TestCase):

    def setUp(self):
        self.tool = MathEvaluatorTool()

    def test_basic_arithmetic(self):
        res = self.tool.execute(expression="2**10 + 24")
        self.assertTrue(res.success)
        self.assertEqual(res.output, "1048")

    def test_math_functions(self):
        res = self.tool.execute(expression="sqrt(144) + factorial(5)")
        self.assertTrue(res.success)
        self.assertEqual(float(res.output), 132.0)

    def test_block_dangerous_code_injection(self):
        # Disallow arbitrary system access
        res = self.tool.execute(expression="__import__('os').system('dir')")
        self.assertFalse(res.success)
        self.assertIn("Lỗi", res.error)

    def test_empty_expression(self):
        res = self.tool.execute(expression="   ")
        self.assertFalse(res.success)


class TestFileInspector(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "safe.txt").write_text("Line 1\nLine 2\nLine 3", encoding="utf-8")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "child.txt").write_text("Child file", encoding="utf-8")
        (self.root / "dummy.pdf").write_bytes(b"%PDF-1.4")
        self.tool = FileInspectorTool(workspace_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_directory(self):
        res = self.tool.execute(action="list", path=".")
        self.assertTrue(res.success)
        self.assertIn("[FILE] safe.txt", res.output)
        self.assertIn("[DIR]  sub", res.output)

    def test_read_file(self):
        res = self.tool.execute(action="read", path="safe.txt", max_lines=2)
        self.assertTrue(res.success)
        self.assertIn("Line 1", res.output)
        self.assertIn("Line 2", res.output)

    def test_block_path_traversal(self):
        res = self.tool.execute(action="read", path="../../windows/win.ini")
        self.assertFalse(res.success)
        self.assertIn("Truy cập ngoài thư mục cho phép bị chặn", res.error)

    def test_block_binary_file(self):
        res = self.tool.execute(action="read", path="dummy.pdf")
        self.assertFalse(res.success)
        self.assertIn("Tệp nhị phân", res.error)


class TestDatabaseInspector(unittest.TestCase):

    def setUp(self):
        self.tool = DatabaseInspectorTool()

    def test_invalid_database(self):
        res = self.tool.execute(database="unknown_db")
        self.assertFalse(res.success)
        self.assertIn("không hợp lệ", res.error)

    def test_inspect_knowledge_db_schema(self):
        res = self.tool.execute(database="knowledge")
        self.assertTrue(res.success)
        self.assertIn("knowledge", res.output.lower())

    def test_block_dangerous_modification_query(self):
        res = self.tool.execute(database="knowledge", query="DROP TABLE knowledge;")
        self.assertFalse(res.success)
        self.assertIn("Truy vấn bị từ chối", res.error)

    def test_safe_select_query(self):
        res = self.tool.execute(database="knowledge", query="SELECT id, topic FROM knowledge LIMIT 2;")
        self.assertTrue(res.success)


class TestPythonRunner(unittest.TestCase):

    def setUp(self):
        self.tool = PythonRunnerTool()

    def test_execute_valid_script(self):
        res = self.tool.execute(code="print(21 * 2)")
        self.assertTrue(res.success)
        self.assertEqual(res.output, "42")

    def test_execution_timeout(self):
        # Infinite loop should hit timeout (bounded to 1s)
        res = self.tool.execute(code="import time\nwhile True: time.sleep(0.1)", timeout=1)
        self.assertFalse(res.success)
        self.assertIn("vượt quá giới hạn thời gian", res.error)

    def test_runtime_syntax_error(self):
        res = self.tool.execute(code="def broken(")
        self.assertFalse(res.success)
        self.assertIn("Lỗi thực thi Python", res.error)


class TestHumanVerificationGate(unittest.TestCase):

    def test_auto_approve_low_risk(self):
        gate = HumanVerificationGate(interactive=True, auto_approve_low_risk=True)
        math_tool = MathEvaluatorTool()
        # LOW risk should auto-approve without calling input
        self.assertTrue(gate.verify(math_tool, {"expression": "1+1"}))

    def test_user_approves_high_risk(self):
        # Simulate user typing 'y'
        gate = HumanVerificationGate(interactive=True, auto_approve_low_risk=False, prompt_callback=lambda _: "y")
        py_tool = PythonRunnerTool()
        self.assertTrue(gate.verify(py_tool, {"code": "print('ok')"}))

    def test_user_rejects_high_risk(self):
        # Simulate user typing 'n'
        gate = HumanVerificationGate(interactive=True, auto_approve_low_risk=False, prompt_callback=lambda _: "n")
        py_tool = PythonRunnerTool()
        self.assertFalse(gate.verify(py_tool, {"code": "print('ok')"}))


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        # Non-interactive gate for tests
        gate = HumanVerificationGate(interactive=False)
        self.registry = ToolRegistry(verification_gate=gate)

    def test_default_tools_registered(self):
        tools = self.registry.list_tools()
        names = [t["name"] for t in tools]
        self.assertIn("math_evaluator", names)
        self.assertIn("file_inspector", names)
        self.assertIn("db_inspector", names)
        self.assertIn("python_runner", names)

    def test_execute_registered_tool(self):
        res = self.registry.execute_tool("math_evaluator", {"expression": "100 / 4"})
        self.assertTrue(res.success)
        self.assertEqual(res.output, "25.0")

    def test_extract_tool_call_from_markdown(self):
        text = """Here is the calculation:
```tool_call
{"tool": "math_evaluator", "args": {"expression": "2**8"}, "purpose": "Calculate power"}
```
"""
        call = self.registry.extract_tool_call(text)
        self.assertIsNotNone(call)
        self.assertEqual(call["tool"], "math_evaluator")
        self.assertEqual(call["args"]["expression"], "2**8")


if __name__ == "__main__":
    unittest.main()
