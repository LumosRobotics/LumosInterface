"""
Grammar loader for LumosInterface IDL.

Loads and caches the Lark grammar file.
"""

from pathlib import Path
from lark import Lark
from typing import Optional


# Global grammar cache
_grammar_cache: Optional[Lark] = None


def load_grammar() -> Lark:
    """
    Load the Lark grammar file.

    Uses a global cache to avoid reloading the grammar multiple times.

    Returns:
        Lark parser instance
    """
    global _grammar_cache

    if _grammar_cache is not None:
        return _grammar_cache

    # Find grammar file relative to this module
    grammar_file = Path(__file__).parent.parent.parent / "grammar" / "message.lark"

    if not grammar_file.exists():
        raise FileNotFoundError(f"Grammar file not found: {grammar_file}")

    with open(grammar_file, 'r') as f:
        grammar_text = f.read()

    # Create Lark parser with LALR algorithm
    parser = Lark(
        grammar_text,
        parser='lalr',
        start='start',
        propagate_positions=True,  # Include line/column info in AST
    )

    _grammar_cache = parser
    return parser


def clear_grammar_cache():
    """Clear the grammar cache. Useful for testing."""
    global _grammar_cache
    _grammar_cache = None
