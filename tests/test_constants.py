"""
Test suite for constant definition parsing.

Tests various constant types, values, and syntax.
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


class TestConstantSyntax:
    """Test constant definition syntax parsing."""

    def test_simple_constant(self, parser):
        """Test basic constant definition."""
        code = "const uint8 MAX_SIZE = 100\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

    def test_multiple_constants(self, parser):
        """Test multiple constant definitions."""
        code = """
const uint8 MAX_SATELLITES = 12
const float32 EARTH_RADIUS_M = 6371000.0
const uint8 VERSION = 1
        """
        tree = parser.parse(code.strip())

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 3

    def test_integer_constant(self, parser):
        """Test integer constant."""
        code = "const uint32 COUNT = 42\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

        # Check for int_const
        int_consts = list(tree.find_data("int_const"))
        assert len(int_consts) == 1

    def test_float_constant(self, parser):
        """Test float constant."""
        code = "const float32 PI = 3.14159\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

        # Check for float_const
        float_consts = list(tree.find_data("float_const"))
        assert len(float_consts) == 1

    def test_negative_integer(self, parser):
        """Test negative integer constant."""
        code = "const int32 OFFSET = -42\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

    def test_negative_float(self, parser):
        """Test negative float constant."""
        code = "const float64 TEMP = -273.15\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

    def test_scientific_notation(self, parser):
        """Test scientific notation in float constants."""
        code = "const float32 SPEED_OF_LIGHT = 3.0e8\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

    def test_constant_with_comment(self, parser):
        """Test constant with inline comment."""
        code = "const uint8 MAX_SIZE = 100  // maximum size\n"
        tree = parser.parse(code)

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1


class TestPrimitiveTypes:
    """Test all primitive type constants."""

    def test_bool_type(self, parser):
        """Test bool constant."""
        code = "const bool DEBUG = 1\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_int8_type(self, parser):
        """Test int8 constant."""
        code = "const int8 VAL = -128\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_int16_type(self, parser):
        """Test int16 constant."""
        code = "const int16 VAL = -1000\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_int32_type(self, parser):
        """Test int32 constant."""
        code = "const int32 VAL = -100000\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_int64_type(self, parser):
        """Test int64 constant."""
        code = "const int64 VAL = -9223372036854775808\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_uint8_type(self, parser):
        """Test uint8 constant."""
        code = "const uint8 VAL = 255\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_uint16_type(self, parser):
        """Test uint16 constant."""
        code = "const uint16 VAL = 65535\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_uint32_type(self, parser):
        """Test uint32 constant."""
        code = "const uint32 VAL = 4294967295\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_uint64_type(self, parser):
        """Test uint64 constant."""
        code = "const uint64 VAL = 18446744073709551615\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_float32_type(self, parser):
        """Test float32 constant."""
        code = "const float32 VAL = 3.14159\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_float64_type(self, parser):
        """Test float64 constant."""
        code = "const float64 VAL = 2.718281828459045\n"
        tree = parser.parse(code)
        assert tree is not None


class TestConstantExtraction:
    """Test extracting constant information from AST."""

    def test_extract_constant_name(self, parser):
        """Test extracting constant name."""
        code = "const uint8 MAX_SIZE = 100\n"
        tree = parser.parse(code)

        const_def = list(tree.find_data("const_def"))[0]
        # Structure: const_def -> primitive_type, CNAME, const_value
        name = const_def.children[1].value
        assert name == "MAX_SIZE"

    def test_extract_constant_type(self, parser):
        """Test extracting constant type."""
        code = "const uint8 MAX_SIZE = 100\n"
        tree = parser.parse(code)

        const_def = list(tree.find_data("const_def"))[0]
        type_node = const_def.children[0]

        # Get the actual type token
        type_value = type_node.children[0].value
        assert type_value == "uint8"

    def test_extract_constant_value(self, parser):
        """Test extracting constant value."""
        code = "const uint8 MAX_SIZE = 100\n"
        tree = parser.parse(code)

        const_def = list(tree.find_data("const_def"))[0]
        value_node = const_def.children[2]

        # Get the value
        value = value_node.children[0].value
        assert value == "100"

    def test_extract_float_value(self, parser):
        """Test extracting float constant value."""
        code = "const float32 PI = 3.14159\n"
        tree = parser.parse(code)

        const_def = list(tree.find_data("const_def"))[0]
        value_node = const_def.children[2]

        # Get the value
        value = value_node.children[0].value
        assert value == "3.14159"


class TestInvalidConstants:
    """Test that invalid constant syntax raises errors."""

    def test_missing_type_rejected(self, parser):
        """Test that missing type is rejected."""
        code = "const MAX_SIZE = 100\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_missing_value_rejected(self, parser):
        """Test that missing value is rejected."""
        code = "const uint8 MAX_SIZE =\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_missing_equals_rejected(self, parser):
        """Test that missing equals is rejected."""
        code = "const uint8 MAX_SIZE 100\n"

        with pytest.raises(LarkError):
            parser.parse(code)

    def test_invalid_type_rejected(self, parser):
        """Test that invalid type is rejected."""
        code = "const string MAX_SIZE = 100\n"

        with pytest.raises(LarkError):
            parser.parse(code)


class TestMixedContent:
    """Test mixing constants with imports."""

    def test_constants_and_imports(self, parser):
        """Test file with both imports and constants."""
        code = """
import common/geometry

const uint8 MAX_SIZE = 100
const float32 THRESHOLD = 0.5
        """
        tree = parser.parse(code.strip())

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 1

        constants = list(tree.find_data("const_def"))
        assert len(constants) == 2

    def test_interleaved_imports_and_constants(self, parser):
        """Test interleaved imports and constants."""
        code = """
import common/geometry
const uint8 MAX_SIZE = 100
import sensors/gps
const float32 THRESHOLD = 0.5
        """
        tree = parser.parse(code.strip())

        imports = list(tree.find_data("import_stmt"))
        assert len(imports) == 2

        constants = list(tree.find_data("const_def"))
        assert len(constants) == 2


class TestConstantTestFiles:
    """Test parsing of constant test files."""

    def test_valid_constant_files(self, parser):
        """Test all valid constant test files parse successfully."""
        valid_files = [
            "constants_basic.msg",
            "constants_all_types.msg",
            "constants_negative.msg",
            "constants_scientific.msg",
            "constants_with_comments.msg",
            "constants_and_imports.msg",
        ]

        for filename in valid_files:
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

    def test_invalid_constant_files(self, parser):
        """Test that invalid constant files raise errors."""
        invalid_files = [
            "const_missing_type.msg",
            "const_missing_value.msg",
            "const_missing_equals.msg",
            "const_invalid_type.msg",
        ]

        for filename in invalid_files:
            file_path = TEST_DIR / "invalid" / filename

            if not file_path.exists():
                continue

            with open(file_path) as f:
                content = f.read()

            with pytest.raises(LarkError):
                parser.parse(content)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_integer(self, parser):
        """Test very large integer constant."""
        code = "const uint64 BIG = 18446744073709551615\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_very_small_float(self, parser):
        """Test very small float constant."""
        code = "const float64 TINY = 1.23e-308\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_zero_value(self, parser):
        """Test zero constant."""
        code = "const uint8 ZERO = 0\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_uppercase_name(self, parser):
        """Test uppercase constant name (convention)."""
        code = "const uint8 MAX_SIZE = 100\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_mixed_case_name(self, parser):
        """Test mixed case constant name (valid but not convention)."""
        code = "const uint8 MaxSize = 100\n"
        tree = parser.parse(code)
        assert tree is not None

    def test_lowercase_name(self, parser):
        """Test lowercase constant name (valid but not convention)."""
        code = "const uint8 max_size = 100\n"
        tree = parser.parse(code)
        assert tree is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
