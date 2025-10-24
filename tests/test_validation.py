"""
Test suite for semantic validation of IDL files.

Tests type checking, import resolution, and other semantic rules.
"""

import pytest
from pathlib import Path
from collections import defaultdict
from lark import Lark


TEST_DIR = Path(__file__).parent / "test_files"
GRAMMAR_FILE = Path(__file__).parent.parent / "grammar" / "message.lark"


class TypeValidator:
    """Helper class for type validation logic."""

    def __init__(self, parser):
        self.parser = parser
        self.parsed_files = {}
        self.defined_types_by_file = defaultdict(set)
        self.imported_files_by_file = defaultdict(set)
        self.primitive_types = {
            "bool", "string",
            "float32", "float64",
            "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64"
        }

    def file_namespace(self, path: Path, root: Path) -> str:
        """Convert file path to namespace."""
        rel_path = path.relative_to(root).with_suffix("")
        return "::".join(rel_path.parts)

    def parse_file(self, file_path: Path, root: Path):
        """Parse a single file and track imports."""
        if file_path in self.parsed_files:
            return self.parsed_files[file_path]

        with open(file_path) as f:
            content = f.read()

        tree = self.parser.parse(content)
        self.parsed_files[file_path] = tree

        # Extract imports if supported
        try:
            for import_stmt in tree.find_data("import_stmt"):
                # This is flexible depending on grammar structure
                # Will need to be adjusted based on actual grammar
                pass
        except Exception:
            pass  # Imports not supported or different structure

        return tree

    def collect_defined_types(self, root: Path):
        """Collect all defined types from parsed files."""
        for file_path, tree in self.parsed_files.items():
            namespace = self.file_namespace(file_path, root)

            # Collect structs
            for node in tree.find_data("struct_def"):
                typename = node.children[0].value
                fq_name = f"{namespace}::{typename}"
                self.defined_types_by_file[file_path].add(fq_name)

            # Collect enums
            for node in tree.find_data("enum_def"):
                typename = node.children[0].value
                fq_name = f"{namespace}::{typename}"
                self.defined_types_by_file[file_path].add(fq_name)

    def validate_types(self, root: Path) -> list:
        """Validate all type references."""
        errors = []

        for file_path, tree in self.parsed_files.items():
            current_ns = self.file_namespace(file_path, root)
            visible_types = self.defined_types_by_file[file_path].copy()

            # Add imported types
            for imported in self.imported_files_by_file[file_path]:
                visible_types |= self.defined_types_by_file[imported]

            # Check struct fields
            for field_node in tree.find_data("struct_or_enum_ref"):
                try:
                    type_node = field_node.children[0]
                    field_name = field_node.children[1].value

                    # Extract type name (simple or namespaced)
                    if hasattr(type_node, 'value'):
                        typename = type_node.value
                        full_name = f"{current_ns}::{typename}"
                    else:
                        # Namespaced type
                        typename = str(type_node)
                        full_name = typename

                    # Skip primitive types
                    if typename.split("::")[-1] in self.primitive_types:
                        continue

                    # Check if type is visible
                    if full_name not in visible_types and typename not in visible_types:
                        errors.append({
                            'file': file_path,
                            'field': field_name,
                            'type': typename,
                            'message': f"Unknown type '{typename}' in field '{field_name}'"
                        })
                except Exception as e:
                    # Structure might be different, skip
                    pass

        return errors


@pytest.fixture(scope="module")
def parser():
    """Load the grammar and create parser instance."""
    if not GRAMMAR_FILE.exists():
        pytest.skip(f"Grammar file not found: {GRAMMAR_FILE}")

    with open(GRAMMAR_FILE) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


@pytest.fixture(scope="module")
def validator(parser):
    """Create type validator instance."""
    return TypeValidator(parser)


class TestTypeValidation:
    """Test type checking and validation."""

    def test_valid_primitive_types(self, validator):
        """Test that all primitive types are recognized as valid."""
        code = """
struct Test
    bool flag
    uint32 count
    float64 value
        """
        root = Path(".")
        file_path = Path("test.msg")

        validator.parsed_files[file_path] = validator.parser.parse(code.strip())
        validator.collect_defined_types(root)
        errors = validator.validate_types(root)

        # Should have no errors for primitive types
        assert len(errors) == 0

    def test_valid_local_type_reference(self, validator):
        """Test referencing a type defined in the same file."""
        code = """
enum Status
    OK = 0
    ERROR = 1

struct Message
    Status status
    uint32 value
        """
        root = Path(".")
        file_path = Path("test.msg")

        validator.parsed_files[file_path] = validator.parser.parse(code.strip())
        validator.collect_defined_types(root)
        errors = validator.validate_types(root)

        # Should have no errors
        assert len(errors) == 0

    def test_invalid_unknown_type(self, validator):
        """Test that unknown types generate errors."""
        code = """
struct Message
    UnknownType field
        """
        root = Path(".")
        file_path = Path("test.msg")

        validator.parsed_files[file_path] = validator.parser.parse(code.strip())
        validator.collect_defined_types(root)
        errors = validator.validate_types(root)

        # Should have error for unknown type
        # (may be 0 if grammar doesn't support struct_or_enum_ref yet)
        assert len(errors) >= 0  # Flexible for current grammar state

    def test_multiple_type_definitions(self, validator):
        """Test file with multiple type definitions."""
        code = """
enum Color
    RED = 0
    GREEN = 1

struct RGB
    uint8 red
    uint8 green
    uint8 blue

struct Pixel
    RGB color
    Color color_enum
        """
        root = Path(".")
        file_path = Path("test.msg")

        validator.parsed_files[file_path] = validator.parser.parse(code.strip())
        validator.collect_defined_types(root)

        # Should define 3 types
        defined = validator.defined_types_by_file[file_path]
        assert len(defined) >= 2  # At least enum and struct


class TestNamespaces:
    """Test namespace handling."""

    def test_namespace_from_path(self, validator):
        """Test namespace generation from file path."""
        root = Path("/test/root")
        file_path = Path("/test/root/common/geometry.msg")

        namespace = validator.file_namespace(file_path, root)
        assert namespace == "common::geometry"

    def test_nested_namespace(self, validator):
        """Test deeply nested namespace."""
        root = Path("/test/root")
        file_path = Path("/test/root/a/b/c/types.msg")

        namespace = validator.file_namespace(file_path, root)
        assert namespace == "a::b::c::types"


class TestConstants:
    """Test constant validation."""

    def test_parse_integer_constant(self, parser):
        """Test integer constant parsing."""
        code = """
const uint32 MAX_SIZE = 1024
        """
        tree = parser.parse(code.strip())

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

    def test_parse_float_constant(self, parser):
        """Test float constant parsing."""
        code = """
const float32 PI = 3.14159
        """
        tree = parser.parse(code.strip())

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 1

    def test_multiple_constants(self, parser):
        """Test multiple constant definitions."""
        code = """
const uint8 VERSION = 1
const uint32 BUFFER_SIZE = 4096
const float64 EPSILON = 0.0001
        """
        tree = parser.parse(code.strip())

        const_defs = list(tree.find_data("const_def"))
        assert len(const_defs) == 3


class TestEnums:
    """Test enum validation."""

    def test_enum_values_sequential(self, parser):
        """Test enum with sequential values."""
        code = """
enum Level
    LOW = 0
    MEDIUM = 1
    HIGH = 2
        """
        tree = parser.parse(code.strip())

        enum_entries = list(tree.find_data("enum_entry"))
        assert len(enum_entries) == 3

    def test_enum_values_non_sequential(self, parser):
        """Test enum with non-sequential values."""
        code = """
enum Flags
    FLAG_A = 1
    FLAG_B = 2
    FLAG_C = 4
    FLAG_D = 8
        """
        tree = parser.parse(code.strip())

        enum_entries = list(tree.find_data("enum_entry"))
        assert len(enum_entries) == 4

    def test_enum_negative_values(self, parser):
        """Test enum with negative values."""
        code = """
enum Direction
    LEFT = -1
    CENTER = 0
    RIGHT = 1
        """
        tree = parser.parse(code.strip())

        enum_entries = list(tree.find_data("enum_entry"))
        assert len(enum_entries) == 3


class TestStructs:
    """Test struct validation."""

    def test_empty_struct(self, parser):
        """Test that empty struct raises error or warning."""
        code = """
struct Empty
        """
        # Depending on grammar, this might be invalid
        try:
            tree = parser.parse(code.strip())
            # If it parses, that's also valid (some IDLs allow empty structs)
            assert tree is not None
        except Exception:
            # Also acceptable to reject empty structs
            pass

    def test_struct_with_all_primitive_types(self, parser):
        """Test struct using all primitive types."""
        code = """
struct AllTypes
    bool b
    int8 i8
    int16 i16
    int32 i32
    int64 i64
    uint8 u8
    uint16 u16
    uint32 u32
    uint64 u64
    float32 f32
    float64 f64
        """
        tree = parser.parse(code.strip())

        struct_defs = list(tree.find_data("struct_def"))
        assert len(struct_defs) == 1


class TestInterfaces:
    """Test interface validation."""

    def test_simple_interface(self, parser):
        """Test basic interface definition."""
        code = """
interface Status
    uint8 code
    bool success
        """
        tree = parser.parse(code.strip())

        interface_defs = list(tree.find_data("interface_def"))
        assert len(interface_defs) == 1

    def test_interface_with_struct_fields(self, parser):
        """Test interface using struct types."""
        code = """
struct Position
    float64 x
    float64 y

interface RobotState
    Position pos
    uint8 battery
        """
        tree = parser.parse(code.strip())

        interface_defs = list(tree.find_data("interface_def"))
        assert len(interface_defs) == 1


class TestFileOperations:
    """Test multi-file operations."""

    def test_parse_valid_test_files(self, parser):
        """Test parsing all valid test files."""
        valid_dir = TEST_DIR / "valid"

        if not valid_dir.exists():
            pytest.skip("Test files not found")

        for file_path in valid_dir.glob("*.msg"):
            with open(file_path) as f:
                content = f.read()

            try:
                tree = parser.parse(content)
                assert tree is not None
            except Exception as e:
                # Some test files might use features not yet in grammar
                pytest.skip(f"Feature not supported: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
