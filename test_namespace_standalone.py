#!/usr/bin/env python3.9
"""
Standalone test for namespace features - no pytest required.
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


def test_using_namespace():
    """Test using namespace statement."""
    parser = load_parser()

    tests = [
        ('using namespace common::geometry', 'simple namespace'),
        ('using namespace std', 'single segment namespace'),
        ('using namespace common::geometry::types', 'multi-level namespace'),
        ('using namespace a::b::c::d::e', 'deeply nested namespace'),
    ]

    passed = 0
    failed = 0

    for code_line, description in tests:
        code = f"{code_line}\n"
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            stmts = list(tree.find_data("using_namespace_stmt"))
            if len(stmts) == 1:
                print(f"✓ using namespace: {description}")
                passed += 1
            else:
                print(f"✗ {description}: expected 1 statement, got {len(stmts)}")
                failed += 1
        except LarkError as e:
            print(f"✗ using namespace {description}: {e}")
            failed += 1

    return passed, failed


def test_namespace_alias():
    """Test namespace alias statement."""
    parser = load_parser()

    tests = [
        ('namespace cg = common::geometry', 'simple alias'),
        ('namespace geo = geometry', 'alias for single segment'),
        ('namespace types = common::geometry::types', 'multi-level alias'),
        ('namespace xyz = a::b::c', 'multi-segment alias'),
    ]

    passed = 0
    failed = 0

    for code_line, description in tests:
        code = f"{code_line}\n"
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            stmts = list(tree.find_data("namespace_alias_stmt"))
            if len(stmts) == 1:
                # Extract alias name and target namespace
                alias_name = stmts[0].children[0].value
                print(f"✓ namespace alias: {description} (alias={alias_name})")
                passed += 1
            else:
                print(f"✗ {description}: expected 1 statement, got {len(stmts)}")
                failed += 1
        except LarkError as e:
            print(f"✗ namespace alias {description}: {e}")
            failed += 1

    return passed, failed


def test_qualified_namespace():
    """Test qualified namespace parsing."""
    parser = load_parser()

    code = """using namespace common::geometry
namespace cg = common::geometry::types
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Find all qualified namespaces
        namespaces = list(tree.find_data("qualified_namespace"))

        if len(namespaces) == 2:
            # Extract namespace segments (filter out :: separators)
            ns1_parts = [child.value for child in namespaces[0].children
                        if hasattr(child, 'value') and child.value != '::']
            ns2_parts = [child.value for child in namespaces[1].children
                        if hasattr(child, 'value') and child.value != '::']

            if ns1_parts == ['common', 'geometry'] and ns2_parts == ['common', 'geometry', 'types']:
                print(f"✓ qualified namespace extraction: {ns1_parts}, {ns2_parts}")
                passed += 1
            else:
                print(f"✗ namespace parts mismatch: {ns1_parts}, {ns2_parts}")
                failed += 1
        else:
            print(f"✗ Expected 2 qualified namespaces, got {len(namespaces)}")
            failed += 1

    except LarkError as e:
        print(f"✗ qualified namespace test: {e}")
        failed += 1

    return passed, failed


def test_qualified_type_in_field():
    """Test qualified type names in struct fields."""
    parser = load_parser()

    code = """struct Transform
    common::geometry::Vector3 position
    common::geometry::Vector3 rotation
    common::geometry::Quaternion orientation
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Find qualified type fields
        qualified_fields = list(tree.find_data("qualified_type_field"))

        if len(qualified_fields) == 3:
            print(f"✓ qualified type fields: {len(qualified_fields)} fields")
            passed += 1
        else:
            print(f"✗ Expected 3 qualified type fields, got {len(qualified_fields)}")
            failed += 1

    except LarkError as e:
        print(f"✗ qualified type in field: {e}")
        failed += 1

    return passed, failed


def test_mixed_qualified_and_simple_types():
    """Test mixing qualified and simple type names."""
    parser = load_parser()

    code = """struct Data
    uint32 id
    Vector3 localPos
    common::geometry::Vector3 worldPos
    float64 timestamp
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        # Count different field types
        primitive_fields = len([f for f in tree.find_data("struct_field")
                               if f.children[0].data == "primitive_type"])
        user_fields = len(list(tree.find_data("user_type_field")))
        qualified_fields = len(list(tree.find_data("qualified_type_field")))

        if primitive_fields == 2 and user_fields == 1 and qualified_fields == 1:
            print(f"✓ mixed types: {primitive_fields} primitive, {user_fields} user, {qualified_fields} qualified")
            passed += 1
        else:
            print(f"✗ mixed types: got {primitive_fields} primitive, {user_fields} user, {qualified_fields} qualified")
            failed += 1

    except LarkError as e:
        print(f"✗ mixed types test: {e}")
        failed += 1

    return passed, failed


def test_full_namespace_example():
    """Test complete example with imports and namespace usage."""
    parser = load_parser()

    code = """import common/geometry

using namespace common::geometry

namespace cg = common::geometry

struct Transform
    Vector3 position
    cg::Vector3 rotation
    common::geometry::Quaternion orientation
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        imports = list(tree.find_data("import_stmt"))
        using_ns = list(tree.find_data("using_namespace_stmt"))
        ns_alias = list(tree.find_data("namespace_alias_stmt"))
        structs = list(tree.find_data("struct_def"))

        if len(imports) == 1 and len(using_ns) == 1 and len(ns_alias) == 1 and len(structs) == 1:
            print(f"✓ full namespace example: all statements parsed")
            passed += 1
        else:
            print(f"✗ full example: got {len(imports)} imports, {len(using_ns)} using ns, {len(ns_alias)} aliases, {len(structs)} structs")
            failed += 1

    except LarkError as e:
        print(f"✗ full namespace example: {e}")
        failed += 1

    return passed, failed


def test_namespace_extraction():
    """Test extracting namespace components."""
    parser = load_parser()

    code = """namespace geo = common::geometry::types
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        alias_stmt = list(tree.find_data("namespace_alias_stmt"))[0]

        # Extract alias name
        alias_name = alias_stmt.children[0].value

        # Extract qualified namespace (filter out :: separators)
        qualified_ns = alias_stmt.children[1]
        ns_parts = [child.value for child in qualified_ns.children
                   if hasattr(child, 'value') and child.value != '::']

        if alias_name == "geo" and ns_parts == ['common', 'geometry', 'types']:
            print(f"✓ namespace extraction: alias={alias_name}, namespace={ns_parts}")
            passed += 1
        else:
            print(f"✗ extraction failed: alias={alias_name}, namespace={ns_parts}")
            failed += 1

    except Exception as e:
        print(f"✗ namespace extraction: {e}")
        failed += 1

    return passed, failed


def test_qualified_type_extraction():
    """Test extracting qualified type components."""
    parser = load_parser()

    code = """struct Test
    common::geometry::Vector3 pos
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        field = list(tree.find_data("qualified_type_field"))[0]

        # Extract qualified type (filter out :: separators)
        qualified_type = field.children[0]
        type_parts = [child.value for child in qualified_type.children
                     if hasattr(child, 'value') and child.value != '::']

        # Extract field name
        field_name = field.children[1].value

        if type_parts == ['common', 'geometry', 'Vector3'] and field_name == 'pos':
            print(f"✓ qualified type extraction: type={type_parts}, field={field_name}")
            passed += 1
        else:
            print(f"✗ extraction failed: type={type_parts}, field={field_name}")
            failed += 1

    except Exception as e:
        print(f"✗ qualified type extraction: {e}")
        failed += 1

    return passed, failed


def test_invalid_namespace_syntax():
    """Test that invalid namespace syntax is rejected."""
    parser = load_parser()

    invalid_tests = [
        ('using namespace', 'missing namespace name'),
        ('namespace = common::geometry', 'missing alias name'),
        ('namespace cg = ', 'missing target namespace'),
    ]

    passed = 0
    failed = 0

    for code_line, description in invalid_tests:
        code = f"{code_line}\n"
        try:
            processed = preprocess(code)
            tree = parser.parse(processed)
            print(f"✗ {description} - should have been rejected!")
            failed += 1
        except LarkError:
            print(f"✓ {description} - correctly rejected")
            passed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Namespace Features Tests")
    print("=" * 70)
    print()

    print("Using Namespace Statement:")
    print("-" * 70)
    results = [test_using_namespace()]

    print()
    print("Namespace Alias Statement:")
    print("-" * 70)
    results.append(test_namespace_alias())

    print()
    print("Qualified Namespace Parsing:")
    print("-" * 70)
    results.append(test_qualified_namespace())

    print()
    print("Qualified Type in Fields:")
    print("-" * 70)
    results.append(test_qualified_type_in_field())

    print()
    print("Mixed Type Names:")
    print("-" * 70)
    results.append(test_mixed_qualified_and_simple_types())

    print()
    print("Full Example:")
    print("-" * 70)
    results.append(test_full_namespace_example())

    print()
    print("Namespace Extraction:")
    print("-" * 70)
    results.append(test_namespace_extraction())

    print()
    print("Qualified Type Extraction:")
    print("-" * 70)
    results.append(test_qualified_type_extraction())

    print()
    print("Invalid Syntax Tests:")
    print("-" * 70)
    results.append(test_invalid_namespace_syntax())

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
