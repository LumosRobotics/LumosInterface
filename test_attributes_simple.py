#!/usr/bin/env python3.9
"""Simple test script for attribute validation."""

import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lumos_idl import IDLProcessor, Config

def test_can_bus_attributes():
    """Test CAN bus attribute validation."""
    print("Testing CAN bus attributes...")

    with tempfile.TemporaryDirectory() as tmpdir:
        idl_file = Path(tmpdir) / "vehicle.msg"
        idl_file.write_text("""
struct VehicleSpeed
    [attributes]
        can_message:
            id: 291
            cycle_time: 100

    float32 speed
        can_signal:
            min: 0.0
            max: 250.0
            scale: 0.01
""")

        config = Config()
        config.search_paths = [Path(tmpdir)]
        config.attributes.enabled_schemas = ["can_bus"]

        processor = IDLProcessor(config)
        result = processor.process_file(str(idl_file))

        if result.success:
            print("✓ CAN bus attributes test PASSED")
            return True
        else:
            print("✗ CAN bus attributes test FAILED")
            for error in result.errors:
                print(f"  {error.message}")
            return False


def test_validation_attributes():
    """Test validation attribute schema."""
    print("\nTesting validation attributes...")

    with tempfile.TemporaryDirectory() as tmpdir:
        idl_file = Path(tmpdir) / "sensor.msg"
        idl_file.write_text("""
struct Temperature
    [attributes]
        packed: true

    float32 celsius
        range:
            min: -40.0
            max: 125.0
        units: "C"
""")

        config = Config()
        config.search_paths = [Path(tmpdir)]
        config.attributes.enabled_schemas = ["validation"]

        processor = IDLProcessor(config)
        result = processor.process_file(str(idl_file))

        if result.success:
            print("✓ Validation attributes test PASSED")
            return True
        else:
            print("✗ Validation attributes test FAILED")
            for error in result.errors:
                print(f"  {error.message}")
            return False


def test_invalid_attribute():
    """Test that invalid attributes are caught."""
    print("\nTesting invalid attribute detection...")

    with tempfile.TemporaryDirectory() as tmpdir:
        idl_file = Path(tmpdir) / "test.msg"
        idl_file.write_text("""
struct Data
    [attributes]
        can_message:
            id: 536870912

    uint32 value
""")

        config = Config()
        config.search_paths = [Path(tmpdir)]
        config.attributes.enabled_schemas = ["can_bus"]

        processor = IDLProcessor(config)
        result = processor.process_file(str(idl_file))

        if not result.success:
            # Should fail - ID is too large
            has_range_error = any("greater than maximum" in e.message for e in result.errors)
            if has_range_error:
                print("✓ Invalid attribute detection test PASSED")
                return True
            else:
                print("✗ Wrong error type")
                for error in result.errors:
                    print(f"  {error.message}")
                return False
        else:
            print("✗ Invalid attribute detection test FAILED - should have failed")
            return False


def test_no_schemas():
    """Test that validation is skipped when no schemas enabled."""
    print("\nTesting with no schemas enabled...")

    with tempfile.TemporaryDirectory() as tmpdir:
        idl_file = Path(tmpdir) / "test.msg"
        idl_file.write_text("""
struct Data
    [attributes]
        anything: true

    uint32 value
""")

        config = Config()
        config.search_paths = [Path(tmpdir)]
        config.attributes.enabled_schemas = []  # No schemas

        processor = IDLProcessor(config)
        result = processor.process_file(str(idl_file))

        if result.success:
            print("✓ No schemas test PASSED")
            return True
        else:
            print("✗ No schemas test FAILED")
            for error in result.errors:
                print(f"  {error.message}")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("Attribute Validation Tests")
    print("=" * 60)

    results = []
    results.append(test_can_bus_attributes())
    results.append(test_validation_attributes())
    results.append(test_invalid_attribute())
    results.append(test_no_schemas())

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    sys.exit(0 if all(results) else 1)
