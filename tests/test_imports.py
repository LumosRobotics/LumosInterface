"""
Test suite for import statement parsing.

Tests various import path formats, valid and invalid syntax.
"""

import pytest
from pathlib import Path
from lark import Lark
from lark.exceptions import LarkError


GRAMMAR_FILE = Path(__file__).parent.parent / "grammar" / "message.lark"
TEST_DIR = Path(__file__).parent / "test_files"


@pytest.fixture(scope="module")
def parser():
    """Load the grammar and create parser instance."""
    if not GRAMMAR_FILE.exists():
        pytest.skip(f"Grammar file not found: {GRAMMAR_FILE}")

    with open(GRAMMAR_FILE) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


class TestImportSyntax:
    """Test import statement syntax parsing."""

    def test_simple_import(self, parser):
        """Test basic single import."""
        code = "import common/geometry\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_multiple_imports(self, parser):
        """Test multiple import statements."""
        code = """
import common/geometry
import common/constants
import sensors/gps
        """
        tree = parser.parse(code.strip())

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 3

    def test_nested_path(self, parser):
        """Test deeply nested import paths."""
        code = "import sensors/gps/v2/types\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_dots_in_segments(self, parser):
        """Test that dots are allowed in path segments."""
        code = "import common/geo.types\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_multiple_dots_in_segments(self, parser):
        """Test multiple dots in path segments."""
        code = "import a.b.c/d.e.f/file.name\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_underscores_in_segments(self, parser):
        """Test underscores in path segments."""
        code = "import common/sensor_data\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_numbers_in_segments(self, parser):
        """Test numbers in path segments."""
        code = "import sensors/gps2/types\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_import_with_line_comment(self, parser):
        """Test import with single-line comment."""
        code = """
// This is a comment
import common/geometry  // inline comment
        """
        tree = parser.parse(code.strip())

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_import_with_multiline_comment(self, parser):
        """Test import with multiline comment."""
        code = """
/*
 * Import geometry types
 */
import common/geometry
        """
        tree = parser.parse(code.strip())

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1


class TestImportPathExtraction:
    """Test extracting import path components from AST."""

    def test_extract_single_segment(self, parser):
        """Test extracting path with single segment."""
        code = "import geometry\n"
        tree = parser.parse(code)

        import_stmt = list(tree.find_data("import_stmt"))[0]
        import_path = import_stmt.children[0]

        # Extract path segments
        segments = [child.value for child in import_path.children
                   if hasattr(child, 'value')]

        assert segments == ["geometry"]

    def test_extract_multiple_segments(self, parser):
        """Test extracting path with multiple segments."""
        code = "import common/geometry\n"
        tree = parser.parse(code)

        import_stmt = list(tree.find_data("import_stmt"))[0]
        import_path = import_stmt.children[0]

        # Extract path segments
        segments = [child.value for child in import_path.children
                   if hasattr(child, 'value')]

        assert segments == ["common", "geometry"]

    def test_extract_nested_path(self, parser):
        """Test extracting deeply nested path."""
        code = "import a/b/c/d\n"
        tree = parser.parse(code)

        import_stmt = list(tree.find_data("import_stmt"))[0]
        import_path = import_stmt.children[0]

        # Extract path segments
        segments = [child.value for child in import_path.children
                   if hasattr(child, 'value')]

        assert segments == ["a", "b", "c", "d"]

    def test_path_to_file_resolution(self, parser):
        """Test converting import path to file path."""
        code = "import common/geometry\n"
        tree = parser.parse(code)

        import_stmt = list(tree.find_data("import_stmt"))[0]
        import_path = import_stmt.children[0]

        # Extract path segments
        segments = [child.value for child in import_path.children
                   if hasattr(child, 'value')]

        # Convert to file path
        file_path = "/".join(segments) + ".msg"
        assert file_path == "common/geometry.msg"


class TestInvalidImports:
    """Test that invalid import syntax raises errors."""

    def test_leading_slash_rejected(self, parser):
        """Test that leading slash is rejected."""
        code = "import /common/geometry\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_trailing_slash_rejected(self, parser):
        """Test that trailing slash is rejected."""
        code = "import common/geometry/\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_double_slash_rejected(self, parser):
        """Test that double slash is rejected."""
        code = "import common//geometry\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_segment_starting_with_dot_rejected(self, parser):
        """Test that segment starting with dot is rejected."""
        code = "import .common/geometry\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_empty_path_rejected(self, parser):
        """Test that empty import path is rejected."""
        code = "import\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_just_slash_rejected(self, parser):
        """Test that just slash is rejected."""
        code = "import /\n"

        with pytest.raises(LarkError):
            parser.parse(code)


class TestImportTestFiles:
    """Test parsing of import test files."""

    def test_valid_import_files(self, parser):
        """Test all valid import test files parse successfully."""
        valid_import_files = [
            "imports_simple.msg",
            "imports_multiple.msg",
            "imports_nested.msg",
            "imports_with_dots.msg",
            "imports_with_comments.msg",
        ]

        for filename in valid_import_files:
            file_path = TEST_DIR / "valid" / filename

            if not file_path.exists():
                pytest.skip(f"Test file not found: {filename}")

            with open(file_path) as f:
                content = f.read()

            try:
                tree = parser.parse(content)
                assert tree is not None, f"Parse tree is None for {filename}"
            except LarkError as e:
                pytest.fail(f"Failed to parse {filename}: {e}")

    def test_invalid_import_files(self, parser):
        """Test that invalid import files raise errors."""
        invalid_import_files = [
            "import_leading_slash.msg",
            "import_trailing_slash.msg",
            "import_double_slash.msg",
            "import_starts_with_dot.msg",
            "import_empty_segment.msg",
        ]

        for filename in invalid_import_files:
            file_path = TEST_DIR / "invalid" / filename

            if not file_path.exists():
                continue  # Skip if file doesn't exist

            with open(file_path) as f:
                content = f.read()

            with pytest.raises(LarkError,
                             match=None):  # Just verify it raises an error
                parser.parse(content)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_segment_path(self, parser):
        """Test import with just one segment (no slash)."""
        code = "import geometry\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_very_long_path(self, parser):
        """Test import with many nested segments."""
        code = "import a/b/c/d/e/f/g/h/i/j\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_segment_all_numbers(self, parser):
        """Test segment with all numbers (but not starting with number)."""
        code = "import v2023/types\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_mixed_dots_underscores(self, parser):
        """Test segment with both dots and underscores."""
        code = "import common/sensor_data.v2\n"
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

    def test_empty_file(self, parser):
        """Test parsing empty file (no imports)."""
        code = ""
        tree = parser.parse(code)

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 0

    def test_only_comments(self, parser):
        """Test file with only comments, no imports."""
        code = """
// Just comments
/* And multiline
   comments */
        """
        tree = parser.parse(code.strip())

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
