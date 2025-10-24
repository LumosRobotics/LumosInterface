#!/usr/bin/env python3.9
"""
Standalone test for type alias (using) parsing - no pytest required.
"""

from lark import Lark
from lark.exceptions import LarkError
from pathlib import Path


def load_parser():
    """Load the grammar file and create parser."""
    grammar_file = Path("grammar/message.lark")

    with open(grammar_file) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


def test_user_examples():
    """Test the exact examples from the user."""
    parser = load_parser()

    code = """using GPSCoordinate = float64
using Timestamp = uint64
using DeviceId = uint32
"""

    passed = 0
    failed = 0

    try:
        tree = parser.parse(code)
        using_defs = list(tree.find_data("using_def"))
        if len(using_defs) == 3:
            print("✓ User example type aliases (all 3 parsed)")
            passed += 1
        else:
            print(f"✗ User examples: expected 3 aliases, got {len(using_defs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ User examples failed: {e}")
        failed += 1

    return passed, failed


def test_valid_aliases():
    """Test valid type alias cases."""
    parser = load_parser()

    valid_tests = [
        ("using Timestamp = uint64\n", "simple alias"),
        ("using Temperature = float32\n", "float alias"),
        ("using Flag = bool\n", "bool alias"),
        ("using ID = uint32  // comment\n", "with comment"),
        ("using T = int8\n", "single letter name"),
        ("using MyLongTypeName = float64\n", "long name"),
    ]

    passed = 0
    failed = 0

    for code, description in valid_tests:
        try:
            tree = parser.parse(code)
            print(f"✓ {description}")
            passed += 1
        except LarkError as e:
            print(f"✗ {description}: {e}")
            failed += 1

    return passed, failed


def test_all_primitive_types():
    """Test aliasing all primitive types."""
    parser = load_parser()

    types = [
        "bool", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float32", "float64"
    ]

    passed = 0
    failed = 0

    for ptype in types:
        code = f"using MyType = {ptype}\n"
        try:
            tree = parser.parse(code)
            print(f"✓ alias for {ptype}")
            passed += 1
        except LarkError as e:
            print(f"✗ alias for {ptype}: {e}")
            failed += 1

    return passed, failed


def test_invalid_aliases():
    """Test invalid type alias cases - these should fail."""
    parser = load_parser()

    invalid_tests = [
        ("using Timestamp =\n", "missing type"),
        ("using Timestamp uint64\n", "missing equals"),
        ("using = uint64\n", "missing name"),
        ("using Timestamp = string\n", "invalid type"),
        ("using Timestamp = MyCustomType\n", "unknown type"),
    ]

    passed = 0
    failed = 0

    for code, description in invalid_tests:
        try:
            tree = parser.parse(code)
            print(f"✗ {description} - should have been rejected!")
            failed += 1
        except LarkError:
            print(f"✓ {description} - correctly rejected")
            passed += 1

    return passed, failed


def test_mixed_content():
    """Test mixing imports, type aliases, and constants."""
    parser = load_parser()

    code = """import common/geometry

using Timestamp = uint64
using Temperature = float32

const uint8 MAX_DEVICES = 10

using DeviceId = uint32

const float32 THRESHOLD = 0.5
"""

    passed = 0
    failed = 0

    try:
        tree = parser.parse(code)
        imports = list(tree.find_data("import_stmt"))
        aliases = list(tree.find_data("using_def"))
        constants = list(tree.find_data("const_def"))

        if len(imports) == 1 and len(aliases) == 3 and len(constants) == 2:
            print("✓ Mixed imports, aliases, and constants")
            passed += 1
        else:
            print(f"✗ Mixed content: expected 1 import, 3 aliases, 2 constants")
            print(f"   got {len(imports)}, {len(aliases)}, {len(constants)}")
            failed += 1
    except LarkError as e:
        print(f"✗ Mixed content failed: {e}")
        failed += 1

    return passed, failed


def test_alias_extraction():
    """Test extracting type alias details from AST."""
    parser = load_parser()

    tests = [
        ("using Timestamp = uint64\n", "Timestamp", "uint64"),
        ("using Temperature = float32\n", "Temperature", "float32"),
        ("using Flag = bool\n", "Flag", "bool"),
    ]

    passed = 0
    failed = 0

    for code, exp_name, exp_type in tests:
        try:
            tree = parser.parse(code)
            using_def = list(tree.find_data("using_def"))[0]

            # Extract details from AST
            # using_def children: [CNAME, primitive_type, NEWLINE]
            name = using_def.children[0].value
            type_val = using_def.children[1].children[0].value

            if name == exp_name and type_val == exp_type:
                print(f"✓ extraction: {exp_name} = {exp_type}")
                passed += 1
            else:
                print(f"✗ extraction failed: got {name} = {type_val}")
                failed += 1
        except Exception as e:
            print(f"✗ extraction failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    return passed, failed


def test_multiple_aliases():
    """Test multiple type aliases in one file."""
    parser = load_parser()

    code = """using Timestamp = uint64
using Temperature = float32
using Pressure = float32
using DeviceId = uint32
using SensorId = uint16
"""

    passed = 0
    failed = 0

    try:
        tree = parser.parse(code)
        using_defs = list(tree.find_data("using_def"))

        if len(using_defs) == 5:
            print("✓ Multiple type aliases (5 total)")
            passed += 1
        else:
            print(f"✗ Multiple aliases: expected 5, got {len(using_defs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ Multiple aliases failed: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Type Alias (using) Definition Tests")
    print("=" * 70)
    print()

    print("User Example Tests:")
    print("-" * 70)
    results = [test_user_examples()]

    print()
    print("Valid Type Alias Tests:")
    print("-" * 70)
    results.append(test_valid_aliases())

    print()
    print("Primitive Type Tests:")
    print("-" * 70)
    results.append(test_all_primitive_types())

    print()
    print("Invalid Type Alias Tests (should be rejected):")
    print("-" * 70)
    results.append(test_invalid_aliases())

    print()
    print("Mixed Content Tests:")
    print("-" * 70)
    results.append(test_mixed_content())

    print()
    print("Alias Extraction Tests:")
    print("-" * 70)
    results.append(test_alias_extraction())

    print()
    print("Multiple Aliases Tests:")
    print("-" * 70)
    results.append(test_multiple_aliases())

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
