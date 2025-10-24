#!/usr/bin/env python3.9
"""
Standalone test for constant definition parsing - no pytest required.
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

    code = """const uint8 MAX_SATELLITES = 12
const float32 EARTH_RADIUS_M = 6371000.0
const uint8 VERSION = 1
"""

    passed = 0
    failed = 0

    try:
        tree = parser.parse(code)
        const_defs = list(tree.find_data("const_def"))
        if len(const_defs) == 3:
            print("✓ User example constants (all 3 parsed)")
            passed += 1
        else:
            print(f"✗ User examples: expected 3 constants, got {len(const_defs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ User examples failed: {e}")
        failed += 1

    return passed, failed


def test_valid_constants():
    """Test valid constant cases."""
    parser = load_parser()

    valid_tests = [
        ("const uint8 MAX_SIZE = 100\n", "simple integer"),
        ("const float32 PI = 3.14159\n", "simple float"),
        ("const int32 OFFSET = -42\n", "negative integer"),
        ("const float64 TEMP = -273.15\n", "negative float"),
        ("const float32 LIGHT = 3.0e8\n", "scientific notation"),
        ("const uint8 ZERO = 0\n", "zero value"),
        ("const bool DEBUG = 1\n", "bool type"),
        ("const uint64 BIG = 18446744073709551615\n", "large number"),
        ("const uint8 VAL = 100  // comment\n", "with comment"),
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
    """Test all primitive types."""
    parser = load_parser()

    types = [
        "bool", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float32", "float64"
    ]

    passed = 0
    failed = 0

    for ptype in types:
        code = f"const {ptype} VAL = 1\n"
        try:
            tree = parser.parse(code)
            print(f"✓ {ptype} type")
            passed += 1
        except LarkError as e:
            print(f"✗ {ptype} type: {e}")
            failed += 1

    return passed, failed


def test_invalid_constants():
    """Test invalid constant cases - these should fail."""
    parser = load_parser()

    invalid_tests = [
        ("const MAX_SIZE = 100\n", "missing type"),
        ("const uint8 MAX_SIZE =\n", "missing value"),
        ("const uint8 MAX_SIZE 100\n", "missing equals"),
        ("const string MAX = 100\n", "invalid type"),
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
    """Test mixing imports and constants."""
    parser = load_parser()

    code = """import common/geometry

const uint8 MAX_SIZE = 100
const float32 THRESHOLD = 0.5

import sensors/gps

const uint32 BUFFER = 4096
"""

    passed = 0
    failed = 0

    try:
        tree = parser.parse(code)
        imports = list(tree.find_data("import_stmt"))
        constants = list(tree.find_data("const_def"))

        if len(imports) == 2 and len(constants) == 3:
            print("✓ Mixed imports and constants")
            passed += 1
        else:
            print(f"✗ Mixed content: expected 2 imports and 3 constants, got {len(imports)} and {len(constants)}")
            failed += 1
    except LarkError as e:
        print(f"✗ Mixed content failed: {e}")
        failed += 1

    return passed, failed


def test_value_extraction():
    """Test extracting constant details from AST."""
    parser = load_parser()

    tests = [
        ("const uint8 MAX_SIZE = 100\n", "MAX_SIZE", "uint8", "100"),
        ("const float32 PI = 3.14\n", "PI", "float32", "3.14"),
    ]

    passed = 0
    failed = 0

    for code, exp_name, exp_type, exp_value in tests:
        try:
            tree = parser.parse(code)
            const_def = list(tree.find_data("const_def"))[0]

            # Extract details from AST
            # const_def children: [primitive_type, CNAME, const_value, NEWLINE]
            name = const_def.children[1].value
            type_val = const_def.children[0].children[0].value  # primitive_type -> TYPE_TOKEN
            value = const_def.children[2].children[0].value      # const_value -> NUMBER_TOKEN

            if name == exp_name and type_val == exp_type and value == exp_value:
                print(f"✓ extraction: {exp_name} = {exp_value}")
                passed += 1
            else:
                print(f"✗ extraction failed: got {name}, {type_val}, {value}")
                failed += 1
        except Exception as e:
            print(f"✗ extraction failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Constant Definition Tests")
    print("=" * 70)
    print()

    print("User Example Tests:")
    print("-" * 70)
    results = [test_user_examples()]

    print()
    print("Valid Constant Tests:")
    print("-" * 70)
    results.append(test_valid_constants())

    print()
    print("Primitive Type Tests:")
    print("-" * 70)
    results.append(test_all_primitive_types())

    print()
    print("Invalid Constant Tests (should be rejected):")
    print("-" * 70)
    results.append(test_invalid_constants())

    print()
    print("Mixed Content Tests:")
    print("-" * 70)
    results.append(test_mixed_content())

    print()
    print("Value Extraction Tests:")
    print("-" * 70)
    results.append(test_value_extraction())

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
