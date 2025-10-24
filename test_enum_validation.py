#!/usr/bin/env python3.9
"""
Test enum validation functionality.
"""

from lumos_idl import IDLProcessor, Config


def test_valid_enum_explicit_values():
    """Test valid enum with explicit values."""
    print("Test 1: Valid enum with explicit values")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Status
    OK = 0
    WARNING = 1
    ERROR = 2
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Valid enum accepted")
        return True
    else:
        print("✗ Valid enum should be accepted")
        result.print_errors()
        return False


def test_valid_enum_auto_increment():
    """Test valid enum with auto-increment."""
    print("\nTest 2: Valid enum with auto-increment")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Color
    RED
    GREEN
    BLUE
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Auto-increment enum accepted")
        # Verify values were assigned correctly
        for file_path, file_info in result.parsed_files.items():
            for type_info in file_info.defined_types:
                assert type_info.enum_members[0].value == 0
                assert type_info.enum_members[1].value == 1
                assert type_info.enum_members[2].value == 2
                print(f"  Values assigned: RED=0, GREEN=1, BLUE=2")
        return True
    else:
        print("✗ Auto-increment enum should be accepted")
        result.print_errors()
        return False


def test_valid_enum_mixed_values():
    """Test valid enum with mixed explicit and auto-increment."""
    print("\nTest 3: Valid enum with mixed values")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Priority
    LOW = 0
    MEDIUM
    HIGH
    CRITICAL = 100
    URGENT
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Mixed values enum accepted")
        # Verify values
        for file_path, file_info in result.parsed_files.items():
            for type_info in file_info.defined_types:
                members = {m.name: m.value for m in type_info.enum_members}
                assert members["LOW"] == 0
                assert members["MEDIUM"] == 1
                assert members["HIGH"] == 2
                assert members["CRITICAL"] == 100
                assert members["URGENT"] == 101
                print(f"  Values: LOW=0, MEDIUM=1, HIGH=2, CRITICAL=100, URGENT=101")
        return True
    else:
        print("✗ Mixed values enum should be accepted")
        result.print_errors()
        return False


def test_enum_with_storage_type():
    """Test enum with explicit storage type."""
    print("\nTest 4: Enum with explicit storage type")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum TimingMode : uint32
    AlwaysFix = 0
    Auto = 1
    Manual = 2
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Enum with storage type accepted")
        # Verify storage type
        for file_path, file_info in result.parsed_files.items():
            for type_info in file_info.defined_types:
                assert type_info.enum_storage_type == "uint32"
                print(f"  Storage type: {type_info.enum_storage_type}")
        return True
    else:
        print("✗ Enum with storage type should be accepted")
        result.print_errors()
        return False


def test_duplicate_member_names():
    """Test detection of duplicate enum member names."""
    print("\nTest 5: Duplicate enum member names")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Status
    OK = 0
    ERROR = 1
    OK = 2
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly detected duplicate member name")
        for error in result.errors:
            if error.error_type == "duplicate_enum_member_name":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have detected duplicate member name")
        return False


def test_duplicate_member_values():
    """Test detection of duplicate enum values."""
    print("\nTest 6: Duplicate enum values")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Status
    OK = 0
    SUCCESS = 0
    ERROR = 1
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly detected duplicate enum value")
        for error in result.errors:
            if error.error_type == "duplicate_enum_value":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have detected duplicate enum value")
        return False


def test_value_out_of_range_uint8():
    """Test detection of value exceeding uint8 range."""
    print("\nTest 7: Value out of range (uint8)")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Flags : uint8
    SMALL = 100
    LARGE = 300
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly detected out-of-range value")
        for error in result.errors:
            if error.error_type == "enum_value_out_of_range":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have detected out-of-range value")
        return False


def test_negative_value_in_unsigned():
    """Test detection of negative value in unsigned type."""
    print("\nTest 8: Negative value in unsigned type")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Status : uint32
    OK = 0
    ERROR = -1
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly rejected negative value in unsigned type")
        for error in result.errors:
            if error.error_type == "enum_value_out_of_range":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have rejected negative value in unsigned type")
        return False


def test_negative_values_in_signed():
    """Test that negative values work in signed types."""
    print("\nTest 9: Negative values in signed type")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum ErrorCode : int32
    SUCCESS = 0
    TIMEOUT = -1
    NETWORK_ERROR = -2
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Negative values accepted in signed type")
        return True
    else:
        print("✗ Negative values should be accepted in signed type")
        result.print_errors()
        return False


def test_value_at_boundary_int8():
    """Test values at int8 boundaries."""
    print("\nTest 10: Values at int8 boundaries")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Boundary : int8
    MIN = -128
    ZERO = 0
    MAX = 127
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Boundary values accepted")
        return True
    else:
        print("✗ Boundary values should be accepted")
        result.print_errors()
        return False


def test_value_beyond_boundary_int8():
    """Test values beyond int8 boundaries."""
    print("\nTest 11: Values beyond int8 boundaries")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Boundary : int8
    TOO_SMALL = -129
    TOO_LARGE = 128
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly rejected out-of-range values")
        error_count = 0
        for error in result.errors:
            if error.error_type == "enum_value_out_of_range":
                print(f"  - {error.message}")
                error_count += 1
        # Should have 2 errors (one for each value)
        if error_count == 2:
            return True
        else:
            print(f"  Expected 2 errors, got {error_count}")
            return False
    else:
        print("✗ Should have rejected out-of-range values")
        return False


def test_enum_in_struct():
    """Test using enum as a field type in struct."""
    print("\nTest 12: Enum used in struct")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Status
    OK = 0
    ERROR = 1

struct Response
    Status status
    string message
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Enum used in struct successfully")
        return True
    else:
        print("✗ Enum should be usable in struct")
        result.print_errors()
        return False


def test_multiple_enums():
    """Test multiple enum definitions in same file."""
    print("\nTest 13: Multiple enums")
    print("-" * 70)

    processor = IDLProcessor()

    code = """enum Color
    RED = 0
    GREEN = 1
    BLUE = 2

enum Status
    OK = 0
    ERROR = 1

enum Priority : uint8
    LOW = 0
    HIGH = 255
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Multiple enums accepted")
        # Verify all were extracted
        for file_path, file_info in result.parsed_files.items():
            if len(file_info.defined_types) == 3:
                print(f"  Found {len(file_info.defined_types)} enums")
                return True
            else:
                print(f"  Expected 3 enums, found {len(file_info.defined_types)}")
                return False
    else:
        print("✗ Multiple enums should be accepted")
        result.print_errors()
        return False


def test_invalid_storage_type():
    """Test detection of invalid storage type."""
    print("\nTest 14: Invalid storage type")
    print("-" * 70)

    processor = IDLProcessor()

    # This will fail during parsing, not validation
    # because float32 is a valid primitive_type in the grammar
    # but we should still test the validator handles it
    code = """enum Status : float32
    OK = 0
    ERROR = 1
"""

    result = processor.process_string(code, "test.msg")

    # Should fail validation (float not allowed for enum)
    if not result.success:
        print("✓ Correctly rejected float storage type")
        for error in result.errors:
            if error.error_type == "invalid_enum_storage_type":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have rejected float storage type")
        return False


def main():
    """Run all enum validation tests."""
    print("=" * 70)
    print("LumosInterface Enum Validation Tests")
    print("=" * 70)
    print()

    tests = [
        test_valid_enum_explicit_values,
        test_valid_enum_auto_increment,
        test_valid_enum_mixed_values,
        test_enum_with_storage_type,
        test_duplicate_member_names,
        test_duplicate_member_values,
        test_value_out_of_range_uint8,
        test_negative_value_in_unsigned,
        test_negative_values_in_signed,
        test_value_at_boundary_int8,
        test_value_beyond_boundary_int8,
        test_enum_in_struct,
        test_multiple_enums,
        test_invalid_storage_type,
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
        print("✓ All enum validation tests passed!")
        return 0
    else:
        print(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
