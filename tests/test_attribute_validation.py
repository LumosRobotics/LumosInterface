"""
Tests for attribute validation system.

Tests schema-based attribute validation for structs, fields, and enums.
"""

import pytest
from pathlib import Path
from lumos_idl.processor import IDLProcessor
from lumos_idl.config import Config, AttributeConfig


def test_can_bus_attributes_valid(tmp_path):
    """Test valid CAN bus attributes."""
    # Create IDL file with CAN bus attributes
    idl_file = tmp_path / "vehicle.msg"
    idl_file.write_text("""
namespace vehicle

struct VehicleSpeed
    [attributes]
        can_message:
            id: 0x123
            cycle_time: 100
            extended: false
            dlc: 8

    float32 speed
        description: "Vehicle speed in km/h"
        can_signal:
            min: 0.0
            max: 250.0
            scale: 0.01
            offset: 0.0
            unit: "km/h"
            byte_order: "little_endian"

    uint8 gear
        can_signal:
            min: 0.0
            max: 8.0
            scale: 1.0
""")

    # Configure with CAN bus schema enabled
    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["can_bus"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should succeed with no errors
    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_can_bus_attributes_invalid_id(tmp_path):
    """Test invalid CAN message ID (out of range)."""
    idl_file = tmp_path / "vehicle.msg"
    idl_file.write_text("""
namespace vehicle

struct VehicleSpeed
    [attributes]
        can_message:
            id: 0xFFFFFFFF
            cycle_time: 100

    float32 speed
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["can_bus"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should fail - ID exceeds 29-bit max
    assert not result.success
    assert any("greater than maximum" in e.message for e in result.errors)


def test_can_bus_attributes_missing_required(tmp_path):
    """Test missing required CAN signal attributes."""
    idl_file = tmp_path / "vehicle.msg"
    idl_file.write_text("""
namespace vehicle

struct VehicleSpeed
    float32 speed
        can_signal:
            min: 0.0
            max: 250.0
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["can_bus"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should fail - scale is required
    assert not result.success
    assert any("Required property 'scale' missing" in e.message for e in result.errors)


def test_validation_attributes_valid(tmp_path):
    """Test valid validation attributes."""
    idl_file = tmp_path / "sensor.msg"
    idl_file.write_text("""
namespace sensor

struct Temperature
    [attributes]
        packed: true
        version: "1.0"

    float32 celsius
        description: "Temperature in Celsius"
        range:
            min: -40.0
            max: 125.0
        units: "C"

    optional string sensor_id
        length:
            min: 1
            max: 64
        pattern: "^[A-Z0-9_]+$"
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_validation_attributes_invalid_align(tmp_path):
    """Test invalid alignment value."""
    idl_file = tmp_path / "data.msg"
    idl_file.write_text("""
namespace data

struct Data
    [attributes]
        align: 3

    uint32 value
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should fail - align must be power of 2
    assert not result.success
    assert any("not in allowed values" in e.message for e in result.errors)


def test_multiple_schemas(tmp_path):
    """Test using multiple schemas together."""
    idl_file = tmp_path / "vehicle.msg"
    idl_file.write_text("""
namespace vehicle

struct VehicleSpeed
    [attributes]
        can_message:
            id: 0x123
            cycle_time: 100
        packed: true

    float32 speed
        description: "Vehicle speed in km/h"
        range:
            min: 0.0
            max: 250.0
        units: "km/h"
        can_signal:
            min: 0.0
            max: 250.0
            scale: 0.01
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["can_bus", "validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_unknown_attribute_warning(tmp_path):
    """Test warning for unknown attributes."""
    idl_file = tmp_path / "test.msg"
    idl_file.write_text("""
namespace test

struct Data
    [attributes]
        custom_attr: true

    uint32 value
        unknown_field_attr: 42
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]
    config.attributes.warn_unknown_attributes = True

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should have warnings for unknown attributes
    warnings = [e for e in result.errors if e.severity == "warning"]
    assert len(warnings) >= 2
    assert any("Unknown attribute 'custom_attr'" in w.message for w in warnings)
    assert any("Unknown attribute 'unknown_field_attr'" in w.message for w in warnings)


def test_no_schemas_enabled(tmp_path):
    """Test that attributes are ignored when no schemas enabled."""
    idl_file = tmp_path / "test.msg"
    idl_file.write_text("""
namespace test

struct Data
    [attributes]
        anything: true

    uint32 value
        whatever: 42
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = []  # No schemas

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should succeed - no validation when no schemas enabled
    assert result.success


def test_enum_attributes(tmp_path):
    """Test enum-level attributes."""
    idl_file = tmp_path / "status.msg"
    idl_file.write_text("""
namespace status

enum Status: uint8
    [attributes]
        deprecated: true
    IDLE = 0
    RUNNING = 1
    ERROR = 2
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Note: This test might need updates once enum attributes are extracted
    # For now, we expect success since enum attributes use struct_attributes field
    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_invalid_attribute_type(tmp_path):
    """Test invalid attribute value type."""
    idl_file = tmp_path / "test.msg"
    idl_file.write_text("""
namespace test

struct Data
    [attributes]
        packed: "not a boolean"

    uint32 value
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should fail - packed must be boolean
    assert not result.success
    assert any("Expected type" in e.message and "boolean" in e.message for e in result.errors)


def test_range_validation(tmp_path):
    """Test range attribute validation."""
    idl_file = tmp_path / "sensor.msg"
    idl_file.write_text("""
namespace sensor

struct Temperature
    float32 celsius
        range:
            min: -40.0
            max: 125.0

    int16 raw_value
        range:
            min: -32768
            max: 32767
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_length_validation(tmp_path):
    """Test length attribute validation."""
    idl_file = tmp_path / "test.msg"
    idl_file.write_text("""
namespace test

struct Message
    string text
        length:
            min: 1
            max: 1000

    string code
        length:
            max: 64
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_pattern_validation(tmp_path):
    """Test pattern attribute validation."""
    idl_file = tmp_path / "test.msg"
    idl_file.write_text("""
namespace test

struct Identifier
    string uuid
        pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    string code
        pattern: "^[A-Z]{3}[0-9]{4}$"
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["validation"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_can_signal_byte_order(tmp_path):
    """Test CAN signal byte order validation."""
    idl_file = tmp_path / "can.msg"
    idl_file.write_text("""
namespace can

struct CanData
    uint32 value1
        can_signal:
            min: 0.0
            max: 1000.0
            scale: 1.0
            byte_order: "little_endian"

    uint32 value2
        can_signal:
            min: 0.0
            max: 1000.0
            scale: 1.0
            byte_order: "big_endian"
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["can_bus"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    assert result.success, f"Expected success, got errors: {[e.message for e in result.errors]}"


def test_can_signal_invalid_byte_order(tmp_path):
    """Test invalid CAN signal byte order."""
    idl_file = tmp_path / "can.msg"
    idl_file.write_text("""
namespace can

struct CanData
    uint32 value
        can_signal:
            min: 0.0
            max: 1000.0
            scale: 1.0
            byte_order: "invalid_order"
""")

    config = Config()
    config.search_paths = [tmp_path]
    config.attributes.enabled_schemas = ["can_bus"]

    processor = IDLProcessor(config)
    result = processor.process_file(str(idl_file))

    # Should fail - byte_order must be little_endian or big_endian
    assert not result.success
    assert any("not in allowed values" in e.message for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
