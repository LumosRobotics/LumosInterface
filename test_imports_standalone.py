#!/usr/bin/env python3.9
"""
Standalone test for import statement parsing - no pytest required.
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


def test_valid_imports():
    """Test valid import cases."""
    parser = load_parser()

    valid_tests = [
        ("import common/geometry\n", "simple import"),
        ("import common/geometry\nimport common/constants\n", "multiple imports"),
        ("import sensors/gps/v2/types\n", "nested path"),
        ("import common/geo.types\n", "dots in segment"),
        ("import a.b.c/d.e.f/file.name\n", "multiple dots"),
        ("import common/sensor_data\n", "underscores"),
        ("import sensors/gps2\n", "numbers in segment"),
        ("import geometry\n", "single segment"),
        ("import a/b/c/d/e/f/g/h\n", "very long path"),
        ("// comment\nimport common/geometry\n", "with comment"),
        ("/* comment */\nimport common/geometry\n", "with multiline comment"),
        ("", "empty file"),
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


def test_invalid_imports():
    """Test invalid import cases - these should fail."""
    parser = load_parser()

    invalid_tests = [
        ("import /common/geometry\n", "leading slash"),
        ("import common/geometry/\n", "trailing slash"),
        ("import common//geometry\n", "double slash"),
        ("import .common/geometry\n", "starts with dot"),
        ("import /\n", "just slash"),
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


def test_path_extraction():
    """Test extracting path components from AST."""
    parser = load_parser()

    tests = [
        ("import geometry\n", ["geometry"]),
        ("import common/geometry\n", ["common", "geometry"]),
        ("import a/b/c/d\n", ["a", "b", "c", "d"]),
    ]

    passed = 0
    failed = 0

    for code, expected_segments in tests:
        try:
            tree = parser.parse(code)
            import_stmt = list(tree.find_data("import_stmt"))[0]
            import_path_token = import_stmt.children[0]

            # IMPORT_PATH is now a terminal token, split by /
            segments = import_path_token.value.split('/')

            if segments == expected_segments:
                print(f"✓ path extraction: {'/'.join(expected_segments)}")
                passed += 1
            else:
                print(f"✗ path extraction: expected {expected_segments}, got {segments}")
                failed += 1
        except Exception as e:
            print(f"✗ path extraction failed: {e}")
            failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Import Statement Tests")
    print("=" * 70)
    print()

    print("Valid Import Tests:")
    print("-" * 70)
    v_pass, v_fail = test_valid_imports()

    print()
    print("Invalid Import Tests (should be rejected):")
    print("-" * 70)
    i_pass, i_fail = test_invalid_imports()

    print()
    print("Path Extraction Tests:")
    print("-" * 70)
    p_pass, p_fail = test_path_extraction()

    print()
    print("=" * 70)
    total_pass = v_pass + i_pass + p_pass
    total_fail = v_fail + i_fail + p_fail
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
