#!/usr/bin/env python3.9
"""
Standalone test for inline field attributes - no pytest required.
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


def test_single_inline_attribute():
    """Test single inline attribute."""
    parser = load_parser()

    code = """struct Test
    uint32 value @description("A test value")
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        inline_attrs = list(tree.find_data("inline_attribute"))
        if len(inline_attrs) == 1:
            print("✓ single inline attribute")
            passed += 1
        else:
            print(f"✗ expected 1 inline attribute, got {len(inline_attrs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ single inline attribute: {e}")
        failed += 1

    return passed, failed


def test_multiple_inline_attributes():
    """Test multiple inline attributes."""
    parser = load_parser()

    code = """struct GpsData
    GpsFixStatus status @description("GPS fix status"), @size(3), @encoding("utf-8")
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        inline_attrs = list(tree.find_data("inline_attribute"))
        if len(inline_attrs) == 3:
            print("✓ multiple inline attributes (3)")
            passed += 1
        else:
            print(f"✗ expected 3 inline attributes, got {len(inline_attrs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ multiple inline attributes: {e}")
        failed += 1

    return passed, failed


def test_inline_attribute_value_types():
    """Test different value types in inline attributes."""
    parser = load_parser()

    tests = [
        ('@flag(true)', 'boolean true'),
        ('@flag(false)', 'boolean false'),
        ('@size(100)', 'integer'),
        ('@tolerance(0.001)', 'float'),
        ('@name("test")', 'string'),
        ('@desc("""multiline\ntext""")', 'multiline string'),
    ]

    passed = 0
    failed = 0

    for attr, description in tests:
        code = f"""struct Test
    uint32 value {attr}
"""
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            print(f"✓ inline attribute with {description}")
            passed += 1
        except LarkError as e:
            print(f"✗ inline attribute with {description}: {e}")
            failed += 1

    return passed, failed


def test_inline_and_indented_together():
    """Test mixing inline and indented attributes."""
    parser = load_parser()

    code = """struct Sensor
    float32 temperature @unit("celsius"), @range(-40)
        description: "Temperature measurement"
        accuracy: 0.5
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        inline_attrs = list(tree.find_data("inline_attribute"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(inline_attrs) == 2 and len(field_attrs) == 1:
            print(f"✓ mixed inline (2) and indented (1 block) attributes")
            passed += 1
        else:
            print(f"✗ expected 2 inline and 1 indented block, got {len(inline_attrs)} and {len(field_attrs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ mixed attributes: {e}")
        failed += 1

    return passed, failed


def test_inline_on_different_field_types():
    """Test inline attributes on different field types."""
    parser = load_parser()

    code = """struct Mixed
    uint32 id @required(true)
    Vector3 position @unit("meters")
    common::geometry::Point location @coordinate_system("WGS84")
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        inline_attrs = list(tree.find_data("inline_attribute"))

        if len(inline_attrs) == 3:
            print(f"✓ inline attributes on primitive, user, and qualified types")
            passed += 1
        else:
            print(f"✗ expected 3 inline attributes, got {len(inline_attrs)}")
            failed += 1
    except LarkError as e:
        print(f"✗ inline on different types: {e}")
        failed += 1

    return passed, failed


def test_multiple_fields_with_inline():
    """Test multiple fields each with inline attributes."""
    parser = load_parser()

    code = """struct Data
    uint32 id @primary(true)
    float32 value @maxlen(256), @encoding("utf-8")
    float64 timestamp @precision(3)
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Count all field types
        all_fields = list(tree.find_data("struct_field")) + \
                     list(tree.find_data("user_type_field")) + \
                     list(tree.find_data("qualified_type_field"))
        inline_attrs = list(tree.find_data("inline_attribute"))

        if len(all_fields) == 3 and len(inline_attrs) == 4:
            print(f"✓ multiple fields with inline attributes (3 fields, 4 total attrs)")
            passed += 1
        else:
            print(f"✗ expected 3 fields with 4 attrs, got {len(all_fields)} fields and {len(inline_attrs)} attrs")
            failed += 1
    except LarkError as e:
        print(f"✗ multiple fields with inline: {e}")
        failed += 1

    return passed, failed


def test_backwards_compatibility():
    """Test that old indented-only syntax still works."""
    parser = load_parser()

    code = """struct Legacy
    float32 value
        unit: "celsius"
        range: "0-100"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Should have NO inline attributes
        inline_attrs = list(tree.find_data("inline_attribute"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(inline_attrs) == 0 and len(field_attrs) == 1:
            print(f"✓ backwards compatible (indented-only still works)")
            passed += 1
        else:
            print(f"✗ backwards compatibility issue")
            failed += 1
    except LarkError as e:
        print(f"✗ backwards compatibility: {e}")
        failed += 1

    return passed, failed


def test_inline_attribute_extraction():
    """Test extracting inline attribute details."""
    parser = load_parser()

    code = """struct Test
    uint32 value @size(100), @description("test")
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        inline_attrs = list(tree.find_data("inline_attribute"))

        # Extract attribute details
        # inline_attribute has children: [@ token, CNAME token, attribute_value Tree]
        attr1 = inline_attrs[0]
        name1 = attr1.children[1].value  # CNAME (index 1)
        value1_node = attr1.children[2]  # attribute_value tree (index 2)

        attr2 = inline_attrs[1]
        name2 = attr2.children[1].value
        value2_node = attr2.children[2]

        if name1 == "size" and value1_node.data == "int_value" and \
           name2 == "description" and value2_node.data == "string_value":
            print(f"✓ attribute extraction ({name1}={value1_node.data}, {name2}={value2_node.data})")
            passed += 1
        else:
            print(f"✗ extraction failed: {name1}={value1_node.data}, {name2}={value2_node.data}")
            failed += 1
    except Exception as e:
        print(f"✗ attribute extraction: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    return passed, failed


def test_no_attributes_still_valid():
    """Test fields with no attributes at all."""
    parser = load_parser()

    code = """struct Simple
    uint32 id
    float64 value
    bool flag
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Count all field types
        all_fields = list(tree.find_data("struct_field")) + \
                     list(tree.find_data("user_type_field")) + \
                     list(tree.find_data("qualified_type_field"))
        inline_attrs = list(tree.find_data("inline_attribute"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(all_fields) == 3 and len(inline_attrs) == 0 and len(field_attrs) == 0:
            print(f"✓ fields with no attributes work")
            passed += 1
        else:
            print(f"✗ no-attribute test failed: {len(all_fields)} fields, {len(inline_attrs)} inline, {len(field_attrs)} indented")
            failed += 1
    except LarkError as e:
        print(f"✗ no attributes: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Inline Attribute Tests")
    print("=" * 70)
    print()

    print("Basic Inline Attributes:")
    print("-" * 70)
    results = [test_single_inline_attribute()]
    results.append(test_multiple_inline_attributes())

    print()
    print("Inline Attribute Value Types:")
    print("-" * 70)
    results.append(test_inline_attribute_value_types())

    print()
    print("Mixed Inline and Indented:")
    print("-" * 70)
    results.append(test_inline_and_indented_together())

    print()
    print("Different Field Types:")
    print("-" * 70)
    results.append(test_inline_on_different_field_types())

    print()
    print("Multiple Fields:")
    print("-" * 70)
    results.append(test_multiple_fields_with_inline())

    print()
    print("Backwards Compatibility:")
    print("-" * 70)
    results.append(test_backwards_compatibility())

    print()
    print("Attribute Extraction:")
    print("-" * 70)
    results.append(test_inline_attribute_extraction())

    print()
    print("No Attributes:")
    print("-" * 70)
    results.append(test_no_attributes_still_valid())

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
