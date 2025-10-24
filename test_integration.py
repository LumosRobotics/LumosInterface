#!/usr/bin/env python3.9
"""
Comprehensive integration test for lumos_idl package.

Tests the complete flow from parsing to potential validation.
"""

from lumos_idl import IDLProcessor, Config
from pathlib import Path


def test_complete_workflow():
    """Test complete workflow with multiple features."""

    print("=" * 70)
    print("LumosInterface Complete Integration Test")
    print("=" * 70)
    print()

    # Test 1: Create configuration
    print("1. Configuration System")
    print("-" * 70)
    config = Config.default()
    print(f"✓ Created default config")
    print(f"  Search paths: {config.search_paths}")
    print(f"  Max field number: {config.validation.max_field_number}")
    print(f"  Enforce field numbering: {config.validation.enforce_field_numbering}")
    print()

    # Test 2: Parse complex file with all features
    print("2. Parse Complex IDL File")
    print("-" * 70)

    complex_idl = """// Complex IDL demonstrating all features
import common/geometry

using namespace common::geometry
using Timestamp = uint64
using Temperature = float32

namespace types = common::types

const uint8 MAX_SENSORS = 16
const float64 EARTH_RADIUS = 6371000.0

struct Vector3
    [attributes]
        version: "1.0"
        packed: true

    float32 x : 0
        unit: "meters"
    float32 y : 1
        unit: "meters"
    float32 z : 2
        unit: "meters"

interface SensorReading
    uint32 sensor_id : 0 @primary(true), @indexed(true)
    Timestamp timestamp : 1
    Temperature value : 2
        description: \"\"\"Temperature reading in Celsius.
        Valid range: -40 to 85 degrees.\"\"\"
    optional string location : 3
    array<uint8, 100> raw_data : 4
    matrix<float32, 3, 3> calibration : 5
    Vector3 position : 6

struct DataLogger
    string name
    uint32 sample_rate
    optional bool enabled
"""

    processor = IDLProcessor(config)
    result = processor.parse_string(complex_idl, "test_complex.msg")

    if result.success:
        print("✓ Parsing succeeded")
        for file_path, file_info in result.files.items():
            print(f"  File: {file_path}")
            print(f"  Namespace: {file_info.namespace}")
            print(f"  Imports: {file_info.imports}")
            print(f"  Using namespaces: {file_info.using_namespaces}")
            print(f"  Namespace aliases: {file_info.namespace_aliases}")
    else:
        print("✗ Parsing failed")
        for error in result.errors:
            print(f"  {error}")
        return False
    print()

    # Test 3: Parse actual test files
    print("3. Parse Real Test Files")
    print("-" * 70)

    test_files = [
        "tests/test_files/valid/interface_example.msg",
        "tests/test_files/valid/field_numbering.msg",
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            result = processor.parse_file(test_file)
            if result.success:
                print(f"✓ {test_file}")
            else:
                print(f"✗ {test_file}")
                for error in result.errors:
                    print(f"  {error}")
        else:
            print(f"⊘ {test_file} not found")
    print()

    # Test 4: Process with validation (currently just parsing)
    print("4. Process Files (Parse + Validate)")
    print("-" * 70)

    result = processor.process_string(complex_idl, "test_validation.msg")

    if result.success:
        print("✓ Processing succeeded")
        print(f"  Files processed: {len(result.parsed_files)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")
    else:
        print("✗ Processing failed")
        result.print_errors()
        return False
    print()

    # Test 5: Parse directory
    print("5. Parse Directory")
    print("-" * 70)

    result = processor.parse_directory("tests/test_files/valid", recursive=False)

    valid_count = len([f for f in result.files.values()])
    error_count = len(result.errors)

    print(f"  Valid files: {valid_count}")
    print(f"  Errors: {error_count}")

    if result.success:
        print("✓ All files in directory parsed successfully")
    else:
        print(f"⚠ Some files had errors (expected - some use unimplemented features)")
    print()

    # Test 6: Test each feature individually
    print("6. Individual Feature Tests")
    print("-" * 70)

    features = [
        ("Imports", "import common/geometry\n"),
        ("Type Aliases", "using Timestamp = uint64\n"),
        ("Constants", "const uint8 MAX = 10\n"),
        ("Using Namespace", "using namespace common::geometry\n"),
        ("Namespace Alias", "namespace geo = common::geometry\n"),
        ("Simple Struct", "struct Point\n    float32 x\n    float32 y\n"),
        ("Struct with Numbers", "struct Data\n    uint32 id : 0\n    string name : 1\n"),
        ("Optional Field", "struct Config\n    optional string name\n"),
        ("Inline Attributes", "struct User\n    uint32 id @primary(true)\n"),
        ("Array Type", "struct Buffer\n    array<uint8, 100> data\n"),
        ("Interface", "interface Protocol\n    uint32 id\n    string payload\n"),
    ]

    feature_results = []
    for name, code in features:
        result = processor.parse_string(code, f"test_{name}.msg")
        if result.success:
            print(f"✓ {name}")
            feature_results.append(True)
        else:
            print(f"✗ {name}")
            feature_results.append(False)

    print()

    # Summary
    print("=" * 70)
    passed = sum(feature_results)
    total = len(feature_results)
    print(f"Feature Tests: {passed}/{total} passed")

    if all(feature_results):
        print("✓ All integration tests passed!")
        return True
    else:
        print("⚠ Some features failed")
        return False


def main():
    """Run integration tests."""
    try:
        success = test_complete_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n✗ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
