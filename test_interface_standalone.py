#!/usr/bin/env python3.9
"""
Standalone test for interface type - no pytest required.
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


def test_simple_interface():
    """Test simple interface definition."""
    parser = load_parser()

    code = """interface Position
    float64 lat
    float64 lon
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        if len(interfaces) == 1:
            # Interface name is children[1] (children[0] is INTERFACE token)
            interface_name = interfaces[0].children[1].value
            if interface_name == "Position":
                print("✓ simple interface")
                passed += 1
            else:
                print(f"✗ wrong interface name: {interface_name}")
                failed += 1
        else:
            print(f"✗ expected 1 interface, got {len(interfaces)}")
            failed += 1
    except LarkError as e:
        print(f"✗ simple interface: {e}")
        failed += 1

    return passed, failed


def test_interface_with_attributes():
    """Test interface with [attributes] block."""
    parser = load_parser()

    code = """interface Config
    [attributes]
        version: \"1.0\"
        packed: true
    uint32 id
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        struct_attrs = list(tree.find_data("struct_attributes"))

        if len(interfaces) == 1 and len(struct_attrs) == 1:
            print("✓ interface with [attributes] block")
            passed += 1
        else:
            print(f"✗ interface with attributes failed")
            failed += 1
    except LarkError as e:
        print(f"✗ interface with attributes: {e}")
        failed += 1

    return passed, failed


def test_interface_with_field_numbers():
    """Test interface with field numbering."""
    parser = load_parser()

    code = """interface Data
    uint32 id : 0
    string name : 1
    float64 value : 2
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        field_numbers = list(tree.find_data("field_number"))

        if len(interfaces) == 1 and len(field_numbers) == 3:
            print("✓ interface with field numbering")
            passed += 1
        else:
            print(f"✗ interface with field numbers failed")
            failed += 1
    except LarkError as e:
        print(f"✗ interface with field numbers: {e}")
        failed += 1

    return passed, failed


def test_interface_with_optional():
    """Test interface with optional fields."""
    parser = load_parser()

    code = """interface Sensor
    uint32 id
    optional float64 temperature
    optional string location
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        if len(interfaces) == 1:
            print("✓ interface with optional fields")
            passed += 1
        else:
            print(f"✗ interface with optional failed")
            failed += 1
    except LarkError as e:
        print(f"✗ interface with optional: {e}")
        failed += 1

    return passed, failed


def test_interface_with_collections():
    """Test interface with collection types."""
    parser = load_parser()

    code = """interface SensorData
    array<uint8, 100> data
    matrix<float32, 3, 3> transform
    tensor<float32, 10, 10, 10> grid
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        collection_fields = list(tree.find_data("collection_type_field"))

        if len(interfaces) == 1 and len(collection_fields) == 3:
            print("✓ interface with collection types")
            passed += 1
        else:
            print(f"✗ interface with collections failed")
            failed += 1
    except LarkError as e:
        print(f"✗ interface with collections: {e}")
        failed += 1

    return passed, failed


def test_interface_with_inline_attributes():
    """Test interface with inline attributes."""
    parser = load_parser()

    code = """interface Data
    uint32 id @primary(true), @required(true)
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        inline_attrs = list(tree.find_data("inline_attribute"))

        if len(interfaces) == 1 and len(inline_attrs) == 2:
            print("✓ interface with inline attributes")
            passed += 1
        else:
            print(f"✗ interface with inline attrs failed")
            failed += 1
    except LarkError as e:
        print(f"✗ interface with inline attributes: {e}")
        failed += 1

    return passed, failed


def test_interface_with_indented_attributes():
    """Test interface with indented field attributes."""
    parser = load_parser()

    code = """interface Position
    float64 lat
        description: \"Latitude\"
        unit: \"degrees\"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(interfaces) == 1 and len(field_attrs) == 1:
            print("✓ interface with indented attributes")
            passed += 1
        else:
            print(f"✗ interface with indented attrs failed")
            failed += 1
    except LarkError as e:
        print(f"✗ interface with indented attributes: {e}")
        failed += 1

    return passed, failed


def test_struct_and_interface_together():
    """Test mixing struct and interface in same file."""
    parser = load_parser()

    code = """struct Data
    uint32 id

interface Config
    string name
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        structs = list(tree.find_data("struct_def"))
        interfaces = list(tree.find_data("interface_def"))

        if len(structs) == 1 and len(interfaces) == 1:
            print("✓ struct and interface in same file")
            passed += 1
        else:
            print(f"✗ struct+interface: got {len(structs)} structs, {len(interfaces)} interfaces")
            failed += 1
    except LarkError as e:
        print(f"✗ struct and interface together: {e}")
        failed += 1

    return passed, failed


def test_comprehensive_interface():
    """Test interface with all features combined."""
    parser = load_parser()

    code = """interface SensorData
    [attributes]
        version: \"1.0\"
        packed: true

    uint32 id : 0 @primary(true)
    optional float64 temperature : 1
        unit: \"celsius\"
        range: \"-40 to 85\"
    array<uint8, 100> raw_data : 2
    Vector3 position : 3
    common::geometry::Quaternion rotation : 4
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        interfaces = list(tree.find_data("interface_def"))
        struct_attrs = list(tree.find_data("struct_attributes"))
        field_numbers = list(tree.find_data("field_number"))
        inline_attrs = list(tree.find_data("inline_attribute"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(interfaces) == 1 and len(struct_attrs) == 1 and \
           len(field_numbers) == 5 and len(inline_attrs) == 1 and \
           len(field_attrs) == 1:
            print("✓ comprehensive interface with all features")
            passed += 1
        else:
            print(f"✗ comprehensive interface failed")
            failed += 1
    except LarkError as e:
        print(f"✗ comprehensive interface: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Interface Type Tests")
    print("=" * 70)
    print()

    print("Basic Interface:")
    print("-" * 70)
    results = [test_simple_interface()]
    results.append(test_interface_with_attributes())

    print()
    print("Interface with Field Features:")
    print("-" * 70)
    results.append(test_interface_with_field_numbers())
    results.append(test_interface_with_optional())
    results.append(test_interface_with_collections())

    print()
    print("Interface with Attributes:")
    print("-" * 70)
    results.append(test_interface_with_inline_attributes())
    results.append(test_interface_with_indented_attributes())

    print()
    print("Mixed and Comprehensive:")
    print("-" * 70)
    results.append(test_struct_and_interface_together())
    results.append(test_comprehensive_interface())

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
