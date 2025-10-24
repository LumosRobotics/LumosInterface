#!/usr/bin/env python3.9
"""
Standalone test for struct definition parsing - no pytest required.
"""

from lark import Lark
from lark.exceptions import LarkError
from pathlib import Path
from indentation_preprocessor import IndentationPreprocessor


def load_parser():
    """Load the grammar file and create parser."""
    grammar_file = Path("grammar/message.lark")

    with open(grammar_file) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


def preprocess(code):
    """Preprocess indentation."""
    preprocessor = IndentationPreprocessor()
    return preprocessor.process(code)


def test_user_example():
    """Test the exact example from the user."""
    parser = load_parser()

    code = '''struct Position
    [attributes]
        attribute0: true
        attribute2: "hello"
    float64 lat
        description: "Longitude in degrees"
        unit: "deg"
    float64 lon
        description: "Latitude in degrees"
        unit: "deg"
'''

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        struct_defs = list(tree.find_data("struct_def"))
        if len(struct_defs) == 1:
            print("✓ User example struct with [attributes] block")
            passed += 1
        else:
            print(f"✗ User example: expected 1 struct, got {len(struct_defs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ User example failed: {e}")
        failed += 1

    return passed, failed


def test_simple_structs():
    """Test simple struct definitions."""
    parser = load_parser()

    valid_tests = [
        ("""struct Point
    float32 x
    float32 y
    float32 z
""", "simple struct"),
        ("""struct Single
    uint32 value
""", "struct with one field"),
        ("""struct AllPrimitives
    bool b
    int32 i
    uint64 u
    float32 f
""", "struct with multiple types"),
    ]

    passed = 0
    failed = 0

    for code, description in valid_tests:
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            print(f"✓ {description}")
            passed += 1
        except LarkError as e:
            print(f"✗ {description}: {e}")
            failed += 1

    return passed, failed


def test_struct_with_attributes():
    """Test struct with [attributes] block."""
    parser = load_parser()

    code = """struct Test
    [attributes]
        packed: true
        aligned: 8
        version: "1.0"
    uint32 value
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        struct_attrs = list(tree.find_data("struct_attributes"))
        if len(struct_attrs) == 1:
            print("✓ Struct with [attributes] block")
            passed += 1
        else:
            print(f"✗ Attributes: expected 1 block, got {len(struct_attrs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ Struct with attributes failed: {e}")
        failed += 1

    return passed, failed


def test_field_attributes():
    """Test fields with attribute blocks."""
    parser = load_parser()

    code = """struct Sensor
    float32 temperature
        unit: "celsius"
        range: "-40 to 85"
    float32 pressure
        unit: "hPa"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        field_attrs = list(tree.find_data("field_attributes"))
        if len(field_attrs) == 2:
            print("✓ Fields with attribute blocks")
            passed += 1
        else:
            print(f"✗ Field attributes: expected 2, got {len(field_attrs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ Field attributes failed: {e}")
        failed += 1

    return passed, failed


def test_attribute_value_types():
    """Test all attribute value types."""
    parser = load_parser()

    tests = [
        ('packed: true', 'boolean true'),
        ('enabled: false', 'boolean false'),
        ('size: 42', 'integer'),
        ('tolerance: 0.001', 'float'),
        ('name: "test"', 'string'),
    ]

    passed = 0
    failed = 0

    for attr_line, description in tests:
        code = f"""struct Test
    [attributes]
        {attr_line}
    uint32 value
"""
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            print(f"✓ attribute {description}")
            passed += 1
        except LarkError as e:
            print(f"✗ attribute {description}: {e}")
            failed += 1

    return passed, failed


def test_user_defined_types():
    """Test fields with user-defined types."""
    parser = load_parser()

    code = """struct Vector3
    float32 x
    float32 y
    float32 z

struct Transform
    Vector3 position
    Vector3 rotation
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        structs = list(tree.find_data("struct_def"))
        user_type_fields = list(tree.find_data("user_type_field"))

        if len(structs) == 2 and len(user_type_fields) == 2:
            print("✓ User-defined types in fields")
            passed += 1
        else:
            print(f"✗ User types: got {len(structs)} structs, {len(user_type_fields)} user fields")
            failed += 1
    except LarkError as e:
        print(f"✗ User-defined types failed: {e}")
        failed += 1

    return passed, failed


def test_invalid_structs():
    """Test invalid struct cases."""
    parser = load_parser()

    invalid_tests = [
        ("struct Empty\n", "empty struct (no fields)"),
        ("""struct Test
    [attributes]
    float32 value
""", "empty attributes block"),
    ]

    passed = 0
    failed = 0

    for code, description in invalid_tests:
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            print(f"✗ {description} - should have been rejected!")
            failed += 1
        except LarkError:
            print(f"✓ {description} - correctly rejected")
            passed += 1

    return passed, failed


def test_mixed_content():
    """Test mixing structs with other definitions."""
    parser = load_parser()

    code = """import common/geometry

using Timestamp = uint64

const uint8 VERSION = 1

struct Point
    float32 x
    float32 y

struct Data
    Timestamp time
    Point position
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        imports = list(tree.find_data("import_stmt"))
        aliases = list(tree.find_data("using_def"))
        constants = list(tree.find_data("const_def"))
        structs = list(tree.find_data("struct_def"))

        if len(imports) == 1 and len(aliases) == 1 and len(constants) == 1 and len(structs) == 2:
            print("✓ Mixed content with structs")
            passed += 1
        else:
            print(f"✗ Mixed: got {len(imports)}, {len(aliases)}, {len(constants)}, {len(structs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ Mixed content failed: {e}")
        failed += 1

    return passed, failed


def test_struct_extraction():
    """Test extracting struct details from AST."""
    parser = load_parser()

    code = """struct Point
    float32 x
    float32 y
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        struct_def = list(tree.find_data("struct_def"))[0]

        # Extract struct name (children[1], children[0] is STRUCT token)
        name = struct_def.children[1].value

        # Count fields (they're inside struct_body now)
        fields = list(tree.find_data("struct_field"))

        if name == "Point" and len(fields) == 2:
            print(f"✓ extraction: struct {name} with {len(fields)} fields")
            passed += 1
        else:
            print(f"✗ extraction failed: got {name} with {len(fields)} fields")
            failed += 1
    except Exception as e:
        print(f"✗ extraction failed: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Struct Definition Tests")
    print("=" * 70)
    print()

    print("User Example Test:")
    print("-" * 70)
    results = [test_user_example()]

    print()
    print("Simple Struct Tests:")
    print("-" * 70)
    results.append(test_simple_structs())

    print()
    print("Struct Attributes Tests:")
    print("-" * 70)
    results.append(test_struct_with_attributes())

    print()
    print("Field Attributes Tests:")
    print("-" * 70)
    results.append(test_field_attributes())

    print()
    print("Attribute Value Types:")
    print("-" * 70)
    results.append(test_attribute_value_types())

    print()
    print("User-Defined Types:")
    print("-" * 70)
    results.append(test_user_defined_types())

    print()
    print("Invalid Struct Tests:")
    print("-" * 70)
    results.append(test_invalid_structs())

    print()
    print("Mixed Content Tests:")
    print("-" * 70)
    results.append(test_mixed_content())

    print()
    print("Struct Extraction Tests:")
    print("-" * 70)
    results.append(test_struct_extraction())

    print()
    print("=" * 70)

    total_pass = sum(p for p, f in results)
    total_fail = sum(f for p, f in results)
    total = total_pass + total_fail

    print(f"Results: {total_pass}/{total} tests passed")

    if total_fail > 0:
        print(f"⚠ {total_fail} tests failed")
        return 1
    else:
        print("✓ All tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())
