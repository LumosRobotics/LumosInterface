#!/usr/bin/env python3.9
"""
Test basic validation functionality.
"""

from lumos_idl import IDLProcessor


def test_valid_struct():
    """Test validation of a valid struct."""
    print("Test 1: Valid struct with primitive types")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Point
    float32 x
    float32 y
    float32 z
"""

    result = processor.process_string(code, "test_valid.msg")

    if result.success:
        print("✓ Valid struct passed validation")
        print(f"  Types found: {len(result.get_all_types())}")
        for type_name, type_info in result.get_all_types().items():
            print(f"    - {type_name} ({type_info.kind}) with {len(type_info.fields)} fields")
        return True
    else:
        print("✗ Valid struct failed validation")
        result.print_errors()
        return False


def test_invalid_type_reference():
    """Test validation catches undefined type references."""
    print("\nTest 2: Invalid type reference")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Transform
    Vector3 position
    Vector3 rotation
"""

    result = processor.process_string(code, "test_invalid.msg")

    if not result.success:
        print("✓ Caught undefined type reference")
        print(f"  Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"    - {error.error_type}: {error.message}")
        return True
    else:
        print("✗ Should have caught undefined type")
        return False


def test_valid_with_user_types():
    """Test validation with defined user types."""
    print("\nTest 3: Valid user-defined types")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Vector3
    float32 x
    float32 y
    float32 z

struct Transform
    Vector3 position
    Vector3 rotation
"""

    result = processor.process_string(code, "test_user_types.msg")

    if result.success:
        print("✓ User-defined types validated successfully")
        types = result.get_all_types()
        print(f"  Types found: {len(types)}")
        for type_name, type_info in types.items():
            print(f"    - {type_name}: {len(type_info.fields)} fields")
        return True
    else:
        print("✗ User-defined types failed validation")
        result.print_errors()
        return False


def test_interface_validation():
    """Test validation of interface types."""
    print("\nTest 4: Interface validation")
    print("-" * 70)

    processor = IDLProcessor()

    code = """interface SensorData
    uint32 id : 0
    float64 temperature : 1
    string location : 2
"""

    result = processor.process_string(code, "test_interface.msg")

    if result.success:
        print("✓ Interface validated successfully")
        types = result.get_all_types()
        for type_name, type_info in types.items():
            print(f"  - {type_name} ({type_info.kind})")
            for field in type_info.fields:
                print(f"      {field.type_name} {field.name} : {field.field_number}")
        return True
    else:
        print("✗ Interface validation failed")
        result.print_errors()
        return False


def test_optional_fields():
    """Test validation with optional fields."""
    print("\nTest 5: Optional fields")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Config
    string name
    optional uint32 timeout
    optional string description
"""

    result = processor.process_string(code, "test_optional.msg")

    if result.success:
        print("✓ Optional fields validated successfully")
        types = result.get_all_types()
        for type_name, type_info in types.items():
            for field in type_info.fields:
                optional_str = " (optional)" if field.optional else ""
                print(f"  - {field.type_name} {field.name}{optional_str}")
        return True
    else:
        print("✗ Optional fields validation failed")
        result.print_errors()
        return False


def test_symbol_table():
    """Test symbol table population."""
    print("\nTest 6: Symbol table")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Point
    float32 x
    float32 y

struct Line
    Point start
    Point end

interface Data
    uint32 id
    string name
"""

    result = processor.process_string(code, "test_symbols.msg")

    if result.success:
        # Access symbol table through validator
        symbol_table = processor.validator.get_symbol_table()
        stats = symbol_table.statistics()

        print("✓ Symbol table populated")
        print(f"  Types: {stats['types']}")
        print(f"  Files: {stats['files']}")
        print(f"  Namespaces: {stats['namespaces']}")

        print("\n  Registered types:")
        for type_name in symbol_table.types.keys():
            print(f"    - {type_name}")

        return True
    else:
        print("✗ Symbol table test failed")
        result.print_errors()
        return False


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("LumosInterface Validation Tests")
    print("=" * 70)
    print()

    tests = [
        test_valid_struct,
        test_invalid_type_reference,
        test_valid_with_user_types,
        test_interface_validation,
        test_optional_fields,
        test_symbol_table,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print()
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All validation tests passed!")
        return 0
    else:
        print(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
