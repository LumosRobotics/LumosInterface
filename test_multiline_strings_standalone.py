#!/usr/bin/env python3.9
"""
Standalone test for multiline string support in attributes - no pytest required.
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


def test_multiline_in_field_attributes():
    """Test multiline strings in field attributes."""
    parser = load_parser()

    code = """struct Position
    float64 lat
    float64 lon
        description: \"\"\"Latitude in degrees
        This description is multiline.
        It can span many lines.\"\"\"
        unit: "deg"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Verify we can extract the multiline string
        entries = list(tree.find_data("attribute_entry"))
        multiline_found = False

        for entry in entries:
            key = entry.children[0].value
            value_node = entry.children[1]
            if value_node.data == "multiline_string_value":
                multiline_found = True
                value = value_node.children[0].value
                # Check it contains the triple quotes and newlines
                if '"""' in value and '\n' in value:
                    print("✓ Multiline string in field attributes")
                    passed += 1
                else:
                    print("✗ Multiline string doesn't contain expected content")
                    failed += 1
                break

        if not multiline_found:
            print("✗ Multiline string value not found in AST")
            failed += 1

    except LarkError as e:
        print(f"✗ Multiline in field attributes failed: {e}")
        failed += 1

    return passed, failed


def test_single_line_triple_quoted():
    """Test single-line triple-quoted strings."""
    parser = load_parser()

    tests = [
        ('note: """Simple string"""', 'single-line triple-quoted'),
        ('text: """With special chars: !@#$%"""', 'triple-quoted with special chars'),
        ('empty: """"""', 'empty triple-quoted string'),
    ]

    passed = 0
    failed = 0

    for attr_line, description in tests:
        code = f"""struct Test
    uint32 value
        {attr_line}
"""
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            print(f"✓ {description}")
            passed += 1
        except LarkError as e:
            print(f"✗ {description}: {e}")
            failed += 1

    return passed, failed


def test_mix_regular_and_multiline():
    """Test mixing regular strings and multiline strings."""
    parser = load_parser()

    code = """struct Sensor
    float32 temp
        unit: "celsius"
        description: \"\"\"Temperature sensor
        Range: -40 to 85°C
        Accuracy: ±0.5°C\"\"\"
        calibrated: true
    float32 humidity
        unit: "%"
        range: "0-100"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Count different value types
        regular_strings = len(list(tree.find_data("string_value")))
        multiline_strings = len(list(tree.find_data("multiline_string_value")))

        if regular_strings == 3 and multiline_strings == 1:
            print(f"✓ Mix of regular ({regular_strings}) and multiline ({multiline_strings}) strings")
            passed += 1
        else:
            print(f"✗ Expected 3 regular and 1 multiline, got {regular_strings} and {multiline_strings}")
            failed += 1

    except LarkError as e:
        print(f"✗ Mix of string types failed: {e}")
        failed += 1

    return passed, failed


def test_multiline_in_struct_attributes():
    """Test multiline strings in struct [attributes] block."""
    parser = load_parser()

    code = """struct Config
    [attributes]
        description: \"\"\"This is a config struct
        with a long description
        spanning multiple lines\"\"\"
        version: "1.0"
    uint32 value
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Find multiline string in struct attributes
        struct_attrs = list(tree.find_data("struct_attributes"))
        if len(struct_attrs) == 1:
            entries = list(tree.find_data("attribute_entry"))
            has_multiline = any(
                e.children[1].data == "multiline_string_value"
                for e in entries
            )
            if has_multiline:
                print("✓ Multiline string in struct [attributes] block")
                passed += 1
            else:
                print("✗ No multiline string found in struct attributes")
                failed += 1
        else:
            print("✗ Struct attributes block not found")
            failed += 1

    except LarkError as e:
        print(f"✗ Multiline in struct attributes failed: {e}")
        failed += 1

    return passed, failed


def test_multiline_indentation_preserved():
    """Test that indentation inside multiline strings is preserved."""
    parser = load_parser()

    code = """struct Code
    uint32 id
        example: \"\"\"Example code:
        if (x > 0) {
            return true;
        }\"\"\"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Extract the multiline string and check indentation is preserved
        for entry in tree.find_data("attribute_entry"):
            value_node = entry.children[1]
            if value_node.data == "multiline_string_value":
                value = value_node.children[0].value
                # The string should contain the indented code
                if '    ' in value:  # Should have spaces from indentation
                    print("✓ Indentation preserved in multiline string")
                    passed += 1
                else:
                    print(f"✗ Indentation not preserved: {repr(value)}")
                    failed += 1
                break
        else:
            print("✗ Multiline string not found")
            failed += 1

    except LarkError as e:
        print(f"✗ Indentation preservation test failed: {e}")
        failed += 1

    return passed, failed


def test_multiline_with_special_chars():
    """Test multiline strings with special characters."""
    parser = load_parser()

    code = """struct Data
    uint32 value
        note: \"\"\"Special chars: "quotes" and 'apostrophes'
        Symbols: @#$%^&*()
        Newlines and tabs work too\"\"\"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        print("✓ Multiline string with special characters")
        passed += 1
    except LarkError as e:
        print(f"✗ Special characters in multiline failed: {e}")
        failed += 1

    return passed, failed


def test_nested_quotes():
    """Test multiline strings containing various quote styles."""
    parser = load_parser()

    code = """struct Example
    uint32 id
        text: \"\"\"This contains "double quotes" inside\"\"\"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)
        print("✓ Multiline string with nested double quotes")
        passed += 1
    except LarkError as e:
        print(f"✗ Nested quotes failed: {e}")
        failed += 1

    return passed, failed


def test_multiline_vs_regular_strings():
    """Test that regular strings still work alongside multiline."""
    parser = load_parser()

    code = """struct Test
    uint32 a
        short: "regular"
        long: \"\"\"multiline
        text\"\"\"
    uint32 b
        another: "also regular"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        regular = len(list(tree.find_data("string_value")))
        multiline = len(list(tree.find_data("multiline_string_value")))

        if regular == 2 and multiline == 1:
            print("✓ Regular and multiline strings coexist")
            passed += 1
        else:
            print(f"✗ Expected 2 regular and 1 multiline, got {regular} and {multiline}")
            failed += 1

    except LarkError as e:
        print(f"✗ Coexistence test failed: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Multiline String Tests")
    print("=" * 70)
    print()

    print("Basic Multiline String Tests:")
    print("-" * 70)
    results = [test_multiline_in_field_attributes()]

    print()
    print("Single-Line Triple-Quoted Tests:")
    print("-" * 70)
    results.append(test_single_line_triple_quoted())

    print()
    print("Mixed String Types:")
    print("-" * 70)
    results.append(test_mix_regular_and_multiline())

    print()
    print("Struct Attributes:")
    print("-" * 70)
    results.append(test_multiline_in_struct_attributes())

    print()
    print("Indentation Preservation:")
    print("-" * 70)
    results.append(test_multiline_indentation_preserved())

    print()
    print("Special Characters:")
    print("-" * 70)
    results.append(test_multiline_with_special_chars())

    print()
    print("Nested Quotes:")
    print("-" * 70)
    results.append(test_nested_quotes())

    print()
    print("Coexistence Tests:")
    print("-" * 70)
    results.append(test_multiline_vs_regular_strings())

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
