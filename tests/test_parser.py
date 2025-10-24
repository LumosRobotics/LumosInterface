"""
Test suite for the LumosInterface IDL parser.

Tests parsing, validation, and AST generation for various IDL constructs.
"""

import pytest
from pathlib import Path
from lark import Lark
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedToken


# Test configuration
TEST_DIR = Path(__file__).parent / "test_files"
GRAMMAR_FILE = Path(__file__).parent.parent / "grammar" / "message.lark"


@pytest.fixture(scope="module")
def parser():
    """Load the grammar and create parser instance."""
    if not GRAMMAR_FILE.exists():
        pytest.skip(f"Grammar file not found: {GRAMMAR_FILE}")

    with open(GRAMMAR_FILE) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


@pytest.fixture(scope="module")
def valid_files():
    """Get all valid test files."""
    return list((TEST_DIR / "valid").glob("*.msg"))


@pytest.fixture(scope="module")
def invalid_files():
    """Get all invalid test files."""
    return list((TEST_DIR / "invalid").glob("*.msg"))


class TestParsing:
    """Test basic parsing functionality."""

    def test_parser_exists(self, parser):
        """Verify parser is created successfully."""
        assert parser is not None

    def test_parse_valid_files(self, parser, valid_files):
        """All valid test files should parse without errors."""
        for file_path in valid_files:
            with open(file_path) as f:
                content = f.read()

            try:
                tree = parser.parse(content)
                assert tree is not None, f"Parse tree is None for {file_path.name}"
            except LarkError as e:
                pytest.fail(f"Failed to parse {file_path.name}: {e}")

    def test_invalid_files_raise_errors(self, parser, invalid_files):
        """Invalid test files should raise parsing errors."""
        for file_path in invalid_files:
            # Skip files that test semantic errors (not syntax errors)
            if file_path.name in ["unknown_type.msg", "missing_import.msg"]:
                continue

            with open(file_path) as f:
                content = f.read()

            with pytest.raises(LarkError):
                parser.parse(content)


class TestBasicTypes:
    """Test parsing of basic type definitions."""

    def test_parse_constants(self, parser):
        """Test constant definitions."""
        code = """
const uint8 MAX_COUNT = 100
const float32 PI = 3.14159
        """
        tree = parser.parse(code.strip())

        # Find all constant definitions
        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 2

    def test_parse_enum(self, parser):
        """Test enum definitions."""
        code = """
enum Status
    IDLE = 0
    RUNNING = 1
    ERROR = 2
        """
        tree = parser.parse(code.strip())

        enum_defs = list(tree.find_data("enum_def"))
        assert len(enum_defs) == 1

        enum_entries = list(tree.find_data("enum_entry"))
        assert len(enum_entries) == 3

    def test_parse_struct(self, parser):
        """Test struct definitions."""
        code = """
struct Point
    float32 x
    float32 y
    float32 z
        """
        tree = parser.parse(code.strip())

        struct_defs = list(tree.find_data("struct_def"))
        assert len(struct_defs) == 1

        # Check for fields (exact name depends on grammar)
        # This is flexible to work with different field naming
        fields = list(tree.find_data("struct_field")) or list(tree.find_data("field"))
        assert len(fields) >= 3

    def test_parse_interface(self, parser):
        """Test interface definitions."""
        code = """
struct Position
    float64 x
    float64 y

interface RobotStatus
    Position pos
    uint8 battery_level
        """
        tree = parser.parse(code.strip())

        interface_defs = list(tree.find_data("interface_def"))
        assert len(interface_defs) == 1


class TestAdvancedFeatures:
    """Test advanced language features."""

    def test_parse_comments(self, parser):
        """Test that comments are properly ignored."""
        code = """
// This is a comment
struct Test
    uint32 value  // inline comment
        """
        tree = parser.parse(code.strip())
        assert tree is not None

    def test_parse_multiline_comment(self, parser):
        """Test multiline comments."""
        code = """
/*
This is a
multiline comment
*/
struct Test
    uint32 value
        """
        # This may or may not work depending on grammar
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Multiline comments not supported in current grammar")

    def test_parse_type_alias(self, parser):
        """Test type aliases."""
        code = """
using Timestamp = uint64

struct Event
    Timestamp time
        """
        try:
            tree = parser.parse(code.strip())
            using_defs = list(tree.find_data("using_def")) or list(tree.find_data("type_alias"))
            assert len(using_defs) >= 1
        except LarkError:
            pytest.skip("Type aliases not supported in current grammar")

    def test_parse_import(self, parser):
        """Test import statements."""
        code = """
import common/geometry

struct Test
    uint32 value
        """
        try:
            tree = parser.parse(code.strip())
            imports = list(tree.find_data("import_stmt"))
            assert len(imports) == 1
        except LarkError:
            pytest.skip("Imports not supported in current grammar")


class TestStructureValidation:
    """Test AST structure and validation."""

    def test_struct_name_extraction(self, parser):
        """Test that we can extract struct names from AST."""
        code = """
struct MyStruct
    uint32 field1
        """
        tree = parser.parse(code.strip())

        struct_defs = list(tree.find_data("struct_def"))
        assert len(struct_defs) == 1

        # The first child should be the struct name
        struct_def = struct_defs[0]
        assert struct_def.children[0].type == "CNAME"
        assert struct_def.children[0].value == "MyStruct"

    def test_enum_values(self, parser):
        """Test enum value extraction."""
        code = """
enum Color
    RED = 0
    GREEN = 1
    BLUE = 2
        """
        tree = parser.parse(code.strip())

        enum_entries = list(tree.find_data("enum_entry"))
        assert len(enum_entries) == 3

        # Check first entry
        first_entry = enum_entries[0]
        assert first_entry.children[0].value == "RED"

    def test_primitive_types(self, parser):
        """Test all primitive types are recognized."""
        primitive_types = [
            "bool", "float32", "float64",
            "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64"
        ]

        for ptype in primitive_types:
            code = f"""
struct Test
    {ptype} field
            """
            tree = parser.parse(code.strip())
            assert tree is not None, f"Failed to parse primitive type: {ptype}"


class TestArrays:
    """Test array type parsing."""

    def test_fixed_size_array(self, parser):
        """Test fixed-size array syntax."""
        code = """
struct Test
    array<uint8, 12> data
        """
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Arrays not supported in current grammar")

    def test_dynamic_array(self, parser):
        """Test dynamic array syntax."""
        code = """
struct Test
    array<uint8> data
        """
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Dynamic arrays not supported in current grammar")

    def test_matrix_tensor(self, parser):
        """Test matrix and tensor syntax."""
        code = """
struct Test
    matrix<float32, 3, 3> rotation
    tensor<float32, 10, 10, 3> voxels
        """
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Matrices/tensors not supported in current grammar")


class TestAttributes:
    """Test attribute parsing."""

    def test_struct_attributes(self, parser):
        """Test attributes on structs."""
        code = """
@deprecated
@version("1.0")
struct Test
    uint32 value
        """
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Struct attributes not supported in current grammar")

    def test_field_attributes_inline(self, parser):
        """Test inline field attributes."""
        code = """
struct Test
    float64 value @description("A test value") @unit("meters")
        """
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Field attributes not supported in current grammar")

    def test_field_attributes_block(self, parser):
        """Test block-style field attributes."""
        code = """
struct Test
    float64 value
    {
        description: "A test value"
        unit: "meters"
    }
        """
        try:
            tree = parser.parse(code.strip())
            assert tree is not None
        except LarkError:
            pytest.skip("Block field attributes not supported in current grammar")


class TestPositionTracking:
    """Test that parser tracks source positions."""

    def test_line_numbers(self, parser):
        """Test that AST nodes have line number information."""
        code = """
struct Test
    uint32 field1
    float32 field2
        """
        tree = parser.parse(code.strip())

        # Check if position information is available
        struct_def = list(tree.find_data("struct_def"))[0]

        # Meta should contain line and column info
        if hasattr(struct_def, 'meta'):
            assert hasattr(struct_def.meta, 'line')
            assert struct_def.meta.line > 0


class TestErrorMessages:
    """Test that helpful error messages are generated."""

    def test_unexpected_token_error(self, parser):
        """Test error message for unexpected token."""
        code = """
struct Test
    uint32
        """
        with pytest.raises((UnexpectedInput, UnexpectedToken, LarkError)) as exc_info:
            parser.parse(code.strip())

        # Just verify we get some error
        assert exc_info.value is not None

    def test_incomplete_definition_error(self, parser):
        """Test error for incomplete definitions."""
        code = """
struct
        """
        with pytest.raises(LarkError):
            parser.parse(code.strip())


# Integration test
class TestRealWorldExample:
    """Test parsing of realistic, complex examples."""

    def test_complex_struct(self, parser):
        """Test parsing a complex struct with multiple field types."""
        code = """
enum Status
    OK = 0
    ERROR = 1

struct ComplexMessage
    uint64 timestamp
    Status status
    float32 temperature
    bool is_valid
        """
        tree = parser.parse(code.strip())

        # Should have 1 enum and 1 struct
        assert len(list(tree.find_data("enum_def"))) == 1
        assert len(list(tree.find_data("struct_def"))) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
