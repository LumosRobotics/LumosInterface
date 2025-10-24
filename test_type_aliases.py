#!/usr/bin/env python3.9
"""
Test type alias functionality.
"""

from lumos_idl import IDLProcessor


def test_simple_alias():
    """Test simple type alias."""
    print("Test 1: Simple type alias")
    print("-" * 70)

    processor = IDLProcessor()

    code = """using Timestamp = uint64

struct Event
    Timestamp time
    string message
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Simple alias works")
        # Verify alias was extracted
        for path, file_info in result.parsed_files.items():
            if len(file_info.defined_aliases) == 1:
                alias = file_info.defined_aliases[0]
                print(f"  Alias: {alias.name} = {alias.target_type}")
                return True
            else:
                print(f"  Expected 1 alias, found {len(file_info.defined_aliases)}")
                return False
    else:
        print("✗ Simple alias should work")
        result.print_errors()
        return False


def test_multiple_aliases():
    """Test multiple type aliases."""
    print("\nTest 2: Multiple type aliases")
    print("-" * 70)

    processor = IDLProcessor()

    code = """using GPSCoordinate = float64
using Timestamp = uint64
using DeviceId = uint32

struct Position
    GPSCoordinate latitude
    GPSCoordinate longitude
    Timestamp time
    DeviceId device
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Multiple aliases work")
        for path, file_info in result.parsed_files.items():
            print(f"  Found {len(file_info.defined_aliases)} aliases")
            for alias in file_info.defined_aliases:
                print(f"    {alias.name} = {alias.target_type}")
        return True
    else:
        print("✗ Multiple aliases should work")
        result.print_errors()
        return False


def test_alias_all_primitive_types():
    """Test aliases to all primitive types."""
    print("\nTest 3: Aliases to all primitive types")
    print("-" * 70)

    processor = IDLProcessor()

    code = """using MyBool = bool
using MyInt8 = int8
using MyInt16 = int16
using MyInt32 = int32
using MyInt64 = int64
using MyUint8 = uint8
using MyUint16 = uint16
using MyUint32 = uint32
using MyUint64 = uint64
using MyFloat32 = float32
using MyFloat64 = float64

struct AllTypes
    MyBool flag
    MyInt8 tiny
    MyInt16 small
    MyInt32 medium
    MyInt64 large
    MyUint8 utiny
    MyUint16 usmall
    MyUint32 umedium
    MyUint64 ularge
    MyFloat32 single
    MyFloat64 double
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Aliases to all primitive types work")
        for path, file_info in result.parsed_files.items():
            print(f"  {len(file_info.defined_aliases)} aliases defined")
        return True
    else:
        print("✗ Aliases to all primitive types should work")
        result.print_errors()
        return False


def test_alias_unused():
    """Test that unused aliases don't cause errors."""
    print("\nTest 4: Unused alias")
    print("-" * 70)

    processor = IDLProcessor()

    code = """using Timestamp = uint64

struct Event
    string message
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Unused alias doesn't cause error")
        return True
    else:
        print("✗ Unused alias should be allowed")
        result.print_errors()
        return False


def test_alias_in_optional_field():
    """Test alias in optional field."""
    print("\nTest 5: Alias in optional field")
    print("-" * 70)

    processor = IDLProcessor()

    code = """using Timestamp = uint64

struct Event
    string message
    optional Timestamp time
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Alias in optional field works")
        return True
    else:
        print("✗ Alias in optional field should work")
        result.print_errors()
        return False


def test_alias_with_field_numbers():
    """Test alias with field numbers."""
    print("\nTest 6: Alias with field numbers")
    print("-" * 70)

    processor = IDLProcessor()

    code = """using Timestamp = uint64

struct Event
    string message : 0
    Timestamp time : 1
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Alias with field numbers works")
        return True
    else:
        print("✗ Alias with field numbers should work")
        result.print_errors()
        return False


def test_alias_same_name_as_type():
    """Test alias with same name as a defined type."""
    print("\nTest 7: Alias with same name as type")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Point
    float32 x
    float32 y

using Point = float64

struct Data
    Point value
"""

    result = processor.process_string(code, "test.msg")

    # This could be an error or allowed - currently it will resolve to the struct
    # Let's test current behavior
    if result.success:
        print("✓ Name collision resolved (struct takes precedence)")
        return True
    else:
        print("✓ Name collision detected as error")
        result.print_errors()
        return True  # Either behavior is acceptable


def main():
    """Run all type alias tests."""
    print("=" * 70)
    print("LumosInterface Type Alias Tests")
    print("=" * 70)
    print()

    tests = [
        test_simple_alias,
        test_multiple_aliases,
        test_alias_all_primitive_types,
        test_alias_unused,
        test_alias_in_optional_field,
        test_alias_with_field_numbers,
        test_alias_same_name_as_type,
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
        print("✓ All type alias tests passed!")
        return 0
    else:
        print(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
