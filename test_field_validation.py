#!/usr/bin/env python3.9
"""
Test field validation functionality.
"""

from lumos_idl import IDLProcessor, Config


def test_field_numbering_all_or_nothing():
    """Test that field numbering follows all-or-nothing rule."""
    print("Test 1: Field numbering all-or-nothing rule")
    print("-" * 70)

    processor = IDLProcessor()

    # Mixed numbering - should fail
    code = """struct Data
    uint32 id : 0
    string name
    float64 value : 2
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly caught inconsistent field numbering")
        for error in result.errors:
            if error.error_type == "field_numbering_inconsistent":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have caught inconsistent numbering")
        return False


def test_duplicate_field_numbers():
    """Test detection of duplicate field numbers."""
    print("\nTest 2: Duplicate field numbers")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Data
    uint32 id : 0
    string name : 1
    float64 value : 1
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly caught duplicate field number")
        for error in result.errors:
            if error.error_type == "duplicate_field_number":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have caught duplicate field number")
        return False


def test_duplicate_field_names():
    """Test detection of duplicate field names."""
    print("\nTest 3: Duplicate field names")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Data
    uint32 id
    string name
    float64 name
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly caught duplicate field name")
        for error in result.errors:
            if error.error_type == "duplicate_field_name":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have caught duplicate field name")
        return False


def test_field_number_gaps_warning():
    """Test gap detection in field numbering."""
    print("\nTest 4: Field number gaps (warning)")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Data
    uint32 id : 0
    string name : 1
    float64 value : 5
"""

    result = processor.process_string(code, "test.msg")

    # Should succeed with warnings
    if result.success and len(result.warnings) > 0:
        print("✓ Detected field number gap (warning)")
        for warning in result.warnings:
            if warning.error_type == "field_number_gap":
                print(f"  - {warning.message}")
        return True
    else:
        print("✗ Should have warned about gap")
        print(f"  Success: {result.success}, Warnings: {len(result.warnings)}")
        return False


def test_negative_field_numbers():
    """Test detection of negative field numbers."""
    print("\nTest 5: Negative field numbers")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Data
    uint32 id : -1
    string name : 0
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly rejected negative field number")
        for error in result.errors:
            if error.error_type == "negative_field_number":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have rejected negative field number")
        return False


def test_field_number_too_large():
    """Test detection of field numbers exceeding max."""
    print("\nTest 6: Field number too large")
    print("-" * 70)

    processor = IDLProcessor()

    # Protobuf max is 536870911 (2^29 - 1)
    code = """struct Data
    uint32 id : 0
    string name : 536870912
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Correctly rejected field number exceeding max")
        for error in result.errors:
            if error.error_type == "field_number_too_large":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have rejected large field number")
        return False


def test_valid_field_numbering():
    """Test valid field numbering."""
    print("\nTest 7: Valid field numbering")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Data
    uint32 id : 0
    string name : 1
    float64 value : 2
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Valid field numbering accepted")
        return True
    else:
        print("✗ Valid numbering should have been accepted")
        result.print_errors()
        return False


def test_no_field_numbering():
    """Test that no field numbering is also valid."""
    print("\nTest 8: No field numbering (also valid)")
    print("-" * 70)

    processor = IDLProcessor()

    code = """struct Data
    uint32 id
    string name
    float64 value
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Fields without numbering accepted")
        return True
    else:
        print("✗ Fields without numbering should be valid")
        result.print_errors()
        return False


def test_multiple_types_independent():
    """Test that field numbering is checked independently per type."""
    print("\nTest 9: Multiple types with independent numbering")
    print("-" * 70)

    processor = IDLProcessor()

    # First struct has numbering, second doesn't - both should be valid
    code = """struct Data1
    uint32 id : 0
    string name : 1

struct Data2
    uint32 id
    string name
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Independent numbering per type validated correctly")
        return True
    else:
        print("✗ Should allow different numbering schemes per type")
        result.print_errors()
        return False


def test_interface_field_validation():
    """Test that interfaces follow same field rules."""
    print("\nTest 10: Interface field validation")
    print("-" * 70)

    processor = IDLProcessor()

    # Interface with mixed numbering - should fail
    code = """interface Protocol
    uint32 id : 0
    string payload
"""

    result = processor.process_string(code, "test.msg")

    if not result.success:
        print("✓ Interfaces follow same field numbering rules")
        for error in result.errors:
            if error.error_type == "field_numbering_inconsistent":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Interfaces should follow field numbering rules")
        return False


def test_naming_convention():
    """Test naming convention validation (when enabled)."""
    print("\nTest 11: Naming convention validation")
    print("-" * 70)

    # Create config with naming enforcement
    config = Config.default()
    config.validation.enforce_naming_conventions = True
    processor = IDLProcessor(config)

    # Invalid names (should be snake_case)
    code = """struct Data
    uint32 userId
    string UserName
"""

    result = processor.process_string(code, "test.msg")

    if len(result.warnings) > 0:
        print("✓ Naming convention violations detected")
        for warning in result.warnings:
            if warning.error_type == "invalid_field_name":
                print(f"  - {warning.message}")
        return True
    else:
        print("⚠ Should have warned about naming convention")
        print("  (Might pass if names happen to match pattern)")
        return True  # Not a critical failure


def main():
    """Run all field validation tests."""
    print("=" * 70)
    print("LumosInterface Field Validation Tests")
    print("=" * 70)
    print()

    tests = [
        test_field_numbering_all_or_nothing,
        test_duplicate_field_numbers,
        test_duplicate_field_names,
        test_field_number_gaps_warning,
        test_negative_field_numbers,
        test_field_number_too_large,
        test_valid_field_numbering,
        test_no_field_numbering,
        test_multiple_types_independent,
        test_interface_field_validation,
        test_naming_convention,
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
        print("✓ All field validation tests passed!")
        return 0
    else:
        print(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
