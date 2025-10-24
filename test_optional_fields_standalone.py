#!/usr/bin/env python3.9
"""
Standalone test for optional field modifier - no pytest required.
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


def is_optional(field):
    """Check if a field has the optional modifier."""
    return field.children[0].type == "OPTIONAL" if hasattr(field.children[0], "type") else False


def test_optional_primitive_field():
    """Test optional with primitive type."""
    parser = load_parser()

    code = """struct Test
    optional uint32 id
    float64 value
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("struct_field"))

        if len(fields) == 2 and is_optional(fields[0]) and not is_optional(fields[1]):
            print("✓ optional primitive field")
            passed += 1
        else:
            print(f"✗ optional primitive field failed")
            failed += 1
    except LarkError as e:
        print(f"✗ optional primitive: {e}")
        failed += 1

    return passed, failed


def test_optional_user_type_field():
    """Test optional with user-defined type."""
    parser = load_parser()

    code = """struct Test
    optional Vector3 position
    Vector3 velocity
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("user_type_field"))

        if len(fields) == 2 and is_optional(fields[0]) and not is_optional(fields[1]):
            print("✓ optional user-defined type")
            passed += 1
        else:
            print(f"✗ optional user type failed")
            failed += 1
    except LarkError as e:
        print(f"✗ optional user type: {e}")
        failed += 1

    return passed, failed


def test_optional_qualified_type_field():
    """Test optional with qualified type."""
    parser = load_parser()

    code = """struct Test
    optional common::geometry::Vector3 position
    common::geometry::Vector3 velocity
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("qualified_type_field"))

        if len(fields) == 2 and is_optional(fields[0]) and not is_optional(fields[1]):
            print("✓ optional qualified type")
            passed += 1
        else:
            print(f"✗ optional qualified type failed")
            failed += 1
    except LarkError as e:
        print(f"✗ optional qualified type: {e}")
        failed += 1

    return passed, failed


def test_optional_with_inline_attributes():
    """Test optional field with inline attributes."""
    parser = load_parser()

    code = """struct Test
    optional uint32 id @description("Optional ID"), @default(0)
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("struct_field"))
        inline_attrs = list(tree.find_data("inline_attribute"))

        if len(fields) == 1 and is_optional(fields[0]) and len(inline_attrs) == 2:
            print("✓ optional with inline attributes")
            passed += 1
        else:
            print(f"✗ optional with inline attributes failed")
            failed += 1
    except LarkError as e:
        print(f"✗ optional with inline attributes: {e}")
        failed += 1

    return passed, failed


def test_optional_with_indented_attributes():
    """Test optional field with indented attributes."""
    parser = load_parser()

    code = """struct Test
    optional float64 value
        description: "Optional value"
        default: 0.0
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("struct_field"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(fields) == 1 and is_optional(fields[0]) and len(field_attrs) == 1:
            print("✓ optional with indented attributes")
            passed += 1
        else:
            print(f"✗ optional with indented attributes failed")
            failed += 1
    except LarkError as e:
        print(f"✗ optional with indented attributes: {e}")
        failed += 1

    return passed, failed


def test_optional_with_both_attribute_types():
    """Test optional field with both inline and indented attributes."""
    parser = load_parser()

    code = """struct Test
    optional uint32 id @primary(true)
        description: "Primary key"
        auto_increment: true
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("struct_field"))
        inline_attrs = list(tree.find_data("inline_attribute"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(fields) == 1 and is_optional(fields[0]) and \
           len(inline_attrs) == 1 and len(field_attrs) == 1:
            print("✓ optional with both inline and indented attributes")
            passed += 1
        else:
            print(f"✗ optional with both attribute types failed")
            failed += 1
    except LarkError as e:
        print(f"✗ optional with both attributes: {e}")
        failed += 1

    return passed, failed


def test_mixed_optional_and_required():
    """Test struct with mix of optional and required fields."""
    parser = load_parser()

    code = """struct Data
    uint32 required_id
    optional string optional_name
    float64 required_value
    optional Vector3 optional_position
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        all_fields = list(tree.find_data("struct_field")) + \
                     list(tree.find_data("user_type_field")) + \
                     list(tree.find_data("qualified_type_field"))

        optional_count = sum(1 for f in all_fields if is_optional(f))
        required_count = len(all_fields) - optional_count

        if len(all_fields) == 4 and optional_count == 2 and required_count == 2:
            print(f"✓ mixed optional ({optional_count}) and required ({required_count})")
            passed += 1
        else:
            print(f"✗ mixed fields: got {len(all_fields)} total, {optional_count} optional")
            failed += 1
    except LarkError as e:
        print(f"✗ mixed optional/required: {e}")
        failed += 1

    return passed, failed


def test_all_optional_fields():
    """Test struct where all fields are optional."""
    parser = load_parser()

    code = """struct AllOptional
    optional uint32 a
    optional float64 b
    optional Vector3 c
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        all_fields = list(tree.find_data("struct_field")) + \
                     list(tree.find_data("user_type_field")) + \
                     list(tree.find_data("qualified_type_field"))

        all_optional = all(is_optional(f) for f in all_fields)

        if len(all_fields) == 3 and all_optional:
            print("✓ all fields optional")
            passed += 1
        else:
            print(f"✗ all optional failed")
            failed += 1
    except LarkError as e:
        print(f"✗ all optional: {e}")
        failed += 1

    return passed, failed


def test_optional_extraction():
    """Test extracting optional modifier from AST."""
    parser = load_parser()

    code = """struct Test
    optional uint32 opt_field
    uint32 req_field
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        fields = list(tree.find_data("struct_field"))

        # Extract details from first field (optional)
        field1 = fields[0]
        has_optional1 = is_optional(field1)

        # Extract field name - need to account for optional token
        if has_optional1:
            # OPTIONAL, primitive_type, CNAME, ...
            field_name1 = field1.children[2].value
        else:
            # primitive_type, CNAME, ...
            field_name1 = field1.children[1].value

        # Second field (required)
        field2 = fields[1]
        has_optional2 = is_optional(field2)
        field_name2 = field2.children[1].value if not has_optional2 else field2.children[2].value

        if has_optional1 and not has_optional2 and \
           field_name1 == "opt_field" and field_name2 == "req_field":
            print(f"✓ extraction: {field_name1}=optional, {field_name2}=required")
            passed += 1
        else:
            print(f"✗ extraction failed")
            failed += 1
    except Exception as e:
        print(f"✗ optional extraction: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    return passed, failed


def test_backwards_compatibility():
    """Test that structs without optional still work."""
    parser = load_parser()

    code = """struct Legacy
    uint32 id
    float64 value
    Vector3 position
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        all_fields = list(tree.find_data("struct_field")) + \
                     list(tree.find_data("user_type_field")) + \
                     list(tree.find_data("qualified_type_field"))

        any_optional = any(is_optional(f) for f in all_fields)

        if len(all_fields) == 3 and not any_optional:
            print("✓ backwards compatible (no optional keyword)")
            passed += 1
        else:
            print(f"✗ backwards compatibility failed")
            failed += 1
    except LarkError as e:
        print(f"✗ backwards compatibility: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Optional Field Modifier Tests")
    print("=" * 70)
    print()

    print("Basic Optional Fields:")
    print("-" * 70)
    results = [test_optional_primitive_field()]
    results.append(test_optional_user_type_field())
    results.append(test_optional_qualified_type_field())

    print()
    print("Optional with Attributes:")
    print("-" * 70)
    results.append(test_optional_with_inline_attributes())
    results.append(test_optional_with_indented_attributes())
    results.append(test_optional_with_both_attribute_types())

    print()
    print("Mixed Scenarios:")
    print("-" * 70)
    results.append(test_mixed_optional_and_required())
    results.append(test_all_optional_fields())

    print()
    print("Extraction and Compatibility:")
    print("-" * 70)
    results.append(test_optional_extraction())
    results.append(test_backwards_compatibility())

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
