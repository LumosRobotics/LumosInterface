#!/usr/bin/env python3.9
"""
Standalone test for field numbering - no pytest required.
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


def test_sequential_numbering():
    """Test sequential field numbering (0, 1, 2, ...)."""
    parser = load_parser()

    code = """struct Position
    float64 lat : 0
    float64 lon : 1
    float64 altitude : 2
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        if len(field_numbers) == 3:
            # Extract the numbers
            numbers = [int(fn.children[0].value) for fn in field_numbers]
            if numbers == [0, 1, 2]:
                print("✓ sequential numbering (0, 1, 2)")
                passed += 1
            else:
                print(f"✗ wrong numbers: {numbers}")
                failed += 1
        else:
            print(f"✗ expected 3 field numbers, got {len(field_numbers)}")
            failed += 1
    except LarkError as e:
        print(f"✗ sequential numbering: {e}")
        failed += 1

    return passed, failed


def test_sparse_numbering():
    """Test sparse field numbering (gaps allowed)."""
    parser = load_parser()

    code = """struct Data
    uint32 id : 0
    string name : 5
    float64 value : 10
    bool flag : 100
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        if len(field_numbers) == 4:
            numbers = [int(fn.children[0].value) for fn in field_numbers]
            if numbers == [0, 5, 10, 100]:
                print("✓ sparse numbering (0, 5, 10, 100)")
                passed += 1
            else:
                print(f"✗ wrong sparse numbers: {numbers}")
                failed += 1
        else:
            print(f"✗ sparse numbering failed")
            failed += 1
    except LarkError as e:
        print(f"✗ sparse numbering: {e}")
        failed += 1

    return passed, failed


def test_unordered_numbering():
    """Test unordered field numbering (any order)."""
    parser = load_parser()

    code = """struct Config
    string name : 10
    uint32 version : 1
    bool enabled : 5
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        if len(field_numbers) == 3:
            numbers = [int(fn.children[0].value) for fn in field_numbers]
            if numbers == [10, 1, 5]:
                print("✓ unordered numbering (10, 1, 5)")
                passed += 1
            else:
                print(f"✗ wrong unordered numbers: {numbers}")
                failed += 1
        else:
            print(f"✗ unordered numbering failed")
            failed += 1
    except LarkError as e:
        print(f"✗ unordered numbering: {e}")
        failed += 1

    return passed, failed


def test_no_numbering():
    """Test struct without field numbering (all fields unnumbered)."""
    parser = load_parser()

    code = """struct Simple
    uint32 id
    float64 value
    string name
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        if len(field_numbers) == 0:
            print("✓ no field numbering (backwards incompatible)")
            passed += 1
        else:
            print(f"✗ expected 0 field numbers, got {len(field_numbers)}")
            failed += 1
    except LarkError as e:
        print(f"✗ no numbering: {e}")
        failed += 1

    return passed, failed


def test_numbering_with_inline_attributes():
    """Test field numbering with inline attributes."""
    parser = load_parser()

    code = """struct Data
    uint32 id : 0 @primary(true), @required(true)
    string name : 1 @maxlen(256)
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        inline_attrs = list(tree.find_data("inline_attribute"))

        if len(field_numbers) == 2 and len(inline_attrs) == 3:
            print("✓ field numbering with inline attributes")
            passed += 1
        else:
            print(f"✗ numbering with inline attrs: {len(field_numbers)} numbers, {len(inline_attrs)} attrs")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with inline attributes: {e}")
        failed += 1

    return passed, failed


def test_numbering_with_indented_attributes():
    """Test field numbering with indented attributes."""
    parser = load_parser()

    code = """struct Position
    float64 lat : 0
        description: \"Latitude\"
        unit: \"degrees\"
    float64 lon : 1
        description: \"Longitude\"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(field_numbers) == 2 and len(field_attrs) == 2:
            print("✓ field numbering with indented attributes")
            passed += 1
        else:
            print(f"✗ numbering with indented attrs failed")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with indented attributes: {e}")
        failed += 1

    return passed, failed


def test_numbering_with_optional():
    """Test field numbering with optional modifier."""
    parser = load_parser()

    code = """struct Config
    uint32 version : 0
    optional string name : 1
    optional float64 timeout : 2
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        if len(field_numbers) == 3:
            print("✓ field numbering with optional")
            passed += 1
        else:
            print(f"✗ numbering with optional failed")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with optional: {e}")
        failed += 1

    return passed, failed


def test_numbering_with_collections():
    """Test field numbering with collection types."""
    parser = load_parser()

    code = """struct Data
    array<uint8, 100> data : 0
    matrix<float32, 3, 3> transform : 1
    tensor<float32, 10, 10, 10> grid : 2
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        collection_fields = list(tree.find_data("collection_type_field"))

        if len(field_numbers) == 3 and len(collection_fields) == 3:
            print("✓ field numbering with collections")
            passed += 1
        else:
            print(f"✗ numbering with collections failed")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with collections: {e}")
        failed += 1

    return passed, failed


def test_numbering_with_user_types():
    """Test field numbering with user-defined types."""
    parser = load_parser()

    code = """struct Transform
    Vector3 position : 0
    Quaternion rotation : 1
    Vector3 scale : 2
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        user_fields = list(tree.find_data("user_type_field"))

        if len(field_numbers) == 3 and len(user_fields) == 3:
            print("✓ field numbering with user types")
            passed += 1
        else:
            print(f"✗ numbering with user types failed")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with user types: {e}")
        failed += 1

    return passed, failed


def test_numbering_with_qualified_types():
    """Test field numbering with qualified types."""
    parser = load_parser()

    code = """struct Data
    common::geometry::Vector3 position : 0
    common::geometry::Quaternion rotation : 1
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        qualified_fields = list(tree.find_data("qualified_type_field"))

        if len(field_numbers) == 2 and len(qualified_fields) == 2:
            print("✓ field numbering with qualified types")
            passed += 1
        else:
            print(f"✗ numbering with qualified types failed")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with qualified types: {e}")
        failed += 1

    return passed, failed


def test_field_number_extraction():
    """Test extracting field numbers from AST."""
    parser = load_parser()

    code = """struct Test
    uint32 a : 10
    float64 b : 20
    string c : 30
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))

        # Extract actual numbers
        numbers = [int(fn.children[0].value) for fn in field_numbers]

        if numbers == [10, 20, 30]:
            print(f"✓ field number extraction: {numbers}")
            passed += 1
        else:
            print(f"✗ extraction failed: {numbers}")
            failed += 1
    except Exception as e:
        print(f"✗ field number extraction: {e}")
        failed += 1

    return passed, failed


def test_negative_field_numbers():
    """Test that negative field numbers work (parser allows, validation is separate)."""
    parser = load_parser()

    code = """struct Test
    uint32 field : -1
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        if len(field_numbers) == 1:
            num = int(field_numbers[0].children[0].value)
            print(f"✓ negative field number allowed ({num}) - validation is separate concern")
            passed += 1
        else:
            print(f"✗ negative number test failed")
            failed += 1
    except LarkError as e:
        print(f"✗ negative field numbers: {e}")
        failed += 1

    return passed, failed


def test_multiline_string_with_numbering():
    """Test field numbering with multiline string attributes."""
    parser = load_parser()

    code = """struct Position
    float64 lat : 0
    float64 lon : 1
        description: \"\"\"Latitude in degrees
        This description is multiline.\"\"\"
        unit: \"deg\"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field_numbers = list(tree.find_data("field_number"))
        multiline_strings = list(tree.find_data("multiline_string_value"))

        if len(field_numbers) == 2 and len(multiline_strings) == 1:
            print("✓ field numbering with multiline string attributes")
            passed += 1
        else:
            print(f"✗ numbering with multiline strings failed")
            failed += 1
    except LarkError as e:
        print(f"✗ numbering with multiline strings: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Field Numbering Tests")
    print("=" * 70)
    print()

    print("Basic Numbering:")
    print("-" * 70)
    results = [test_sequential_numbering()]
    results.append(test_sparse_numbering())
    results.append(test_unordered_numbering())
    results.append(test_no_numbering())

    print()
    print("Numbering with Attributes:")
    print("-" * 70)
    results.append(test_numbering_with_inline_attributes())
    results.append(test_numbering_with_indented_attributes())

    print()
    print("Numbering with Modifiers:")
    print("-" * 70)
    results.append(test_numbering_with_optional())

    print()
    print("Numbering with Different Field Types:")
    print("-" * 70)
    results.append(test_numbering_with_collections())
    results.append(test_numbering_with_user_types())
    results.append(test_numbering_with_qualified_types())

    print()
    print("Edge Cases:")
    print("-" * 70)
    results.append(test_field_number_extraction())
    results.append(test_negative_field_numbers())
    results.append(test_multiline_string_with_numbering())

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
