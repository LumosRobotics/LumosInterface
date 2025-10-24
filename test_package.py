#!/usr/bin/env python3.9
"""
Test the new lumos_idl package structure.
"""

from lumos_idl import IDLProcessor, Config


def test_simple_parse():
    """Test parsing a simple struct."""
    processor = IDLProcessor()

    code = """struct Point
    float32 x
    float32 y
    float32 z
"""

    result = processor.parse_string(code)

    if result.success:
        print("✓ Simple struct parsing works")
        return True
    else:
        print("✗ Simple struct parsing failed")
        for error in result.errors:
            print(f"  {error}")
        return False


def test_parse_file():
    """Test parsing an actual file."""
    processor = IDLProcessor()

    result = processor.parse_file("tests/test_files/valid/interface_example.msg")

    if result.success:
        print("✓ File parsing works")
        print(f"  Parsed {len(result.files)} file(s)")
        for file_path, file_info in result.files.items():
            print(f"  - {file_path}: namespace={file_info.namespace}")
            print(f"    Imports: {file_info.imports}")
        return True
    else:
        print("✗ File parsing failed")
        for error in result.errors:
            print(f"  {error}")
        return False


def test_config():
    """Test configuration."""
    # Test default config
    config = Config.default()
    print("✓ Default config created")

    # Test config properties
    assert config.validation.enforce_field_numbering == False
    assert config.validation.max_field_number == 536870911
    print("✓ Config properties accessible")

    return True


def test_process_file():
    """Test the process_file method (parse + validate)."""
    processor = IDLProcessor()

    # Use a simple file that doesn't have undefined type references
    code = """struct Point
    float32 x
    float32 y
    float32 z
"""

    result = processor.process_string(code, "test.msg")

    if result.success:
        print("✓ Process file works")
        print(f"  Parsed {len(result.parsed_files)} file(s)")
        return True
    else:
        print("✗ Process file failed")
        result.print_errors()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("LumosInterface Package Structure Tests")
    print("=" * 70)
    print()

    tests = [
        ("Configuration", test_config),
        ("Simple Parse", test_simple_parse),
        ("Parse File", test_parse_file),
        ("Process File", test_process_file),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 70)
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 70)
    print(f"Results: {passed}/{passed + failed} tests passed")

    if failed > 0:
        print(f"⚠ {failed} test(s) failed")
        return 1
    else:
        print("✓ All tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())
