#!/usr/bin/env python3
"""
Simple standalone test runner - no pytest required.
Useful for quick validation during grammar development.
"""

from pathlib import Path
from lark import Lark
from lark.exceptions import LarkError


def load_parser():
    """Load the grammar file and create parser."""
    grammar_file = Path(__file__).parent.parent / "grammar" / "message.lark"

    if not grammar_file.exists():
        print(f"❌ Grammar file not found: {grammar_file}")
        print("   Available grammar files:")
        for f in grammar_file.parent.glob("*.lark*"):
            print(f"   - {f.name}")
        return None

    with open(grammar_file) as f:
        grammar = f.read()

    print(f"✓ Loaded grammar from {grammar_file.name}")
    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


def test_basic_struct(parser):
    """Test basic struct parsing."""
    code = """
struct Point
    float32 x
    float32 y
    float32 z
    """

    try:
        tree = parser.parse(code.strip())
        print("✓ Basic struct parsing")
        return True
    except LarkError as e:
        print(f"❌ Basic struct parsing failed: {e}")
        return False


def test_enum(parser):
    """Test enum parsing."""
    code = """
enum Status
    IDLE = 0
    RUNNING = 1
    ERROR = 2
    """

    try:
        tree = parser.parse(code.strip())
        print("✓ Enum parsing")
        return True
    except LarkError as e:
        print(f"❌ Enum parsing failed: {e}")
        return False


def test_constant(parser):
    """Test constant parsing."""
    code = """
const uint8 MAX_COUNT = 100
const float32 PI = 3.14159
    """

    try:
        tree = parser.parse(code.strip())
        print("✓ Constant parsing")
        return True
    except LarkError as e:
        print(f"❌ Constant parsing failed: {e}")
        return False


def test_interface(parser):
    """Test interface parsing."""
    code = """
struct Position
    float64 x
    float64 y

interface RobotStatus
    Position pos
    uint8 battery
    """

    try:
        tree = parser.parse(code.strip())
        print("✓ Interface parsing")
        return True
    except LarkError as e:
        print(f"❌ Interface parsing failed: {e}")
        return False


def test_comments(parser):
    """Test comment handling."""
    code = """
// This is a comment
struct Test
    uint32 value  // inline comment
    """

    try:
        tree = parser.parse(code.strip())
        print("✓ Comment handling")
        return True
    except LarkError as e:
        print(f"❌ Comment handling failed: {e}")
        return False


def test_all_primitive_types(parser):
    """Test all primitive types."""
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

    try:
        tree = parser.parse(code.strip())
        print("✓ All primitive types")
        return True
    except LarkError as e:
        print(f"❌ Primitive types failed: {e}")
        return False


def test_test_files(parser):
    """Test parsing all valid test files."""
    test_dir = Path(__file__).parent / "test_files" / "valid"

    if not test_dir.exists():
        print(f"⚠ Test directory not found: {test_dir}")
        return True

    passed = 0
    failed = 0

    for file_path in sorted(test_dir.glob("*.msg")):
        with open(file_path) as f:
            content = f.read()

        try:
            tree = parser.parse(content)
            print(f"✓ {file_path.name}")
            passed += 1
        except LarkError as e:
            print(f"❌ {file_path.name}: {e}")
            failed += 1

    if failed == 0 and passed > 0:
        print(f"✓ All test files parsed ({passed} files)")
        return True
    elif failed > 0:
        print(f"⚠ Some test files failed ({passed} passed, {failed} failed)")
        return False
    else:
        return True


def main():
    """Run all simple tests."""
    print("=" * 60)
    print("LumosInterface Parser - Quick Test")
    print("=" * 60)
    print()

    parser = load_parser()
    if not parser:
        return 1

    print()
    print("Running basic tests:")
    print("-" * 60)

    tests = [
        test_basic_struct,
        test_enum,
        test_constant,
        test_interface,
        test_comments,
        test_all_primitive_types,
    ]

    results = [test(parser) for test in tests]

    print()
    print("-" * 60)
    print("Testing valid test files:")
    print("-" * 60)

    test_files_result = test_test_files(parser)
    results.append(test_files_result)

    print()
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ All tests passed ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        failed = total - passed
        print(f"⚠ Some tests failed ({passed} passed, {failed} failed)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
