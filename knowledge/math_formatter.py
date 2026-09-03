"""Math symbols formatter for clean terminal display."""
import re

MATH_REPLACEMENTS = [
    (r"\\leq\b", "≤"),
    (r"\\le\b", "≤"),
    (r"\\geq\b", "≥"),
    (r"\\ge\b", "≥"),
    (r"\\neq\b", "≠"),
    (r"\\ne\b", "≠"),
    (r"\\notin\b", "∉"),
    (r"\\in\b", "∈"),
    (r"\\forall\b", "∀"),
    (r"\\exists\b", "∃"),
    (r"\\infty\b", "∞"),
    (r"\\rightarrow\b", "→"),
    (r"\\to\b", "→"),
    (r"\\leftarrow\b", "←"),
    (r"\\times\b", "×"),
    (r"\\cdot\b", "·"),
    (r"\\pm\b", "±"),
    (r"\\mp\b", "∓"),
    (r"\\approx\b", "≈"),
    (r"\\equiv\b", "≡"),
    (r"\\subseteq\b", "⊆"),
    (r"\\subset\b", "⊂"),
    (r"\\cup\b", "∪"),
    (r"\\cap\b", "∩"),
    (r"\\emptyset\b", "∅"),
    (r"\\dots\b", "..."),
    (r"\\ldots\b", "..."),
    (r"\\cdots\b", "..."),
]

def format_math_symbols(text: str) -> str:
    """Convert raw LaTeX math commands to clean visual Unicode symbols for terminal."""
    if not text:
        return text
    result = text
    for pattern, symbol in MATH_REPLACEMENTS:
        result = re.sub(pattern, symbol, result)
    return result
