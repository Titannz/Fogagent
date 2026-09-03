"""Unit tests for Math Formatter."""
import unittest
from knowledge.math_formatter import format_math_symbols


class TestMathFormatter(unittest.TestCase):

    def test_comparison_symbols(self):
        self.assertEqual(format_math_symbols(r"x \leq 1"), "x ≤ 1")
        self.assertEqual(format_math_symbols(r"y \geq 0"), "y ≥ 0")
        self.assertEqual(format_math_symbols(r"a \neq b"), "a ≠ b")

    def test_set_and_logic_symbols(self):
        self.assertEqual(format_math_symbols(r"\forall n \in \mathbb{N}"), "∀ n ∈ \\mathbb{N}")
        self.assertEqual(format_math_symbols(r"\exists x"), "∃ x")
        self.assertEqual(format_math_symbols(r"A \subset B"), "A ⊂ B")

    def test_arrows_and_operations(self):
        self.assertEqual(format_math_symbols(r"n \to \infty"), "n → ∞")
        self.assertEqual(format_math_symbols(r"a \pm b"), "a ± b")
        self.assertEqual(format_math_symbols(r"A \times B"), "A × B")


if __name__ == "__main__":
    unittest.main()
