# Flexible Attribute System Architecture

## Problem Statement

Different use cases need different metadata on fields:
- **CAN bus**: min, max, scale values for signal encoding
- **ROS2**: QoS settings, topic names
- **Validation**: range constraints, regex patterns
- **UI**: display names, units, formatting
- **Database**: indexes, constraints

We want this extensible **without modifying the grammar** for each new use case.

---

## Solution: Plugin-Based Attribute System

### Core Concept

1. **Grammar stays generic** - supports arbitrary key-value attributes
2. **Attribute schemas** define what's valid for each domain
3. **Plugins** validate and interpret attributes for specific use cases
4. **Code generators** use relevant attributes, ignore others

---

## Current Grammar (Already Flexible!)

Your current grammar already supports attributes:

```
struct Position
    [attributes]
        packed: true
    float64 latitude
        description: "Latitude in degrees"
        range: [-90.0, 90.0]
    float64 longitude
        description: "Longitude in degrees"
        range: [-180.0, 180.0]
```

**This is good!** It's already generic. Now we need to make it **schematized**.

---

## Proposed Architecture

```
lumos_idl/
├── attributes/
│   ├── __init__.py
│   ├── registry.py              # Attribute schema registry
│   ├── validator.py             # Attribute validation
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── can_bus.py          # CAN bus attribute schema
│   │   ├── ros2.py             # ROS2 attribute schema
│   │   ├── validation.py       # Validation attribute schema
│   │   └── custom.py           # User-defined schemas
│   └── config/
│       ├── can_bus.yaml        # CAN bus attribute definitions
│       ├── ros2.yaml           # ROS2 attribute definitions
│       └── custom.yaml         # User project attributes
```

---

## 1. Attribute Schema Definition

**File: `attributes/config/can_bus.yaml`**

```yaml
# CAN Bus Attribute Schema
schema_name: can_bus
version: "1.0"

description: "Attributes for CAN bus signal encoding"

# Field-level attributes
field_attributes:
  can_signal:
    type: object
    required: false
    description: "CAN signal encoding parameters"
    properties:
      min:
        type: float
        required: true
        description: "Minimum physical value"
      max:
        type: float
        required: true
        description: "Maximum physical value"
      scale:
        type: float
        required: true
        description: "Scaling factor (physical = raw * scale + offset)"
      offset:
        type: float
        required: false
        default: 0.0
        description: "Offset value"
      unit:
        type: string
        required: false
        description: "Physical unit (e.g., 'km/h', 'deg')"

  can_message:
    type: object
    required: false
    description: "CAN message configuration"
    properties:
      id:
        type: integer
        required: true
        description: "CAN message ID (hex or decimal)"
        constraints:
          min: 0
          max: 0x1FFFFFFF  # 29-bit extended CAN ID
      cycle_time:
        type: integer
        required: false
        description: "Message cycle time in milliseconds"
      extended:
        type: boolean
        required: false
        default: false
        description: "Use extended 29-bit ID"

# Struct-level attributes
struct_attributes:
  can_message:
    type: object
    required: false
    description: "Mark struct as CAN message"
    properties:
      id:
        type: integer
        required: true
      cycle_time:
        type: integer
        required: false
```

**File: `attributes/config/validation.yaml`**

```yaml
# Validation Attribute Schema
schema_name: validation
version: "1.0"

field_attributes:
  range:
    type: object
    required: false
    properties:
      min:
        type: [number]
        required: true
      max:
        type: [number]
        required: true

  pattern:
    type: string
    required: false
    description: "Regex pattern for string validation"

  length:
    type: object
    required: false
    properties:
      min:
        type: integer
        required: false
      max:
        type: integer
        required: false

  units:
    type: string
    required: false
    description: "Physical units (for documentation)"
```

---

## 2. Using Attributes in IDL

```
# Example: Vehicle speed sensor with CAN encoding
struct VehicleSpeed
    [attributes]
        can_message:
            id: 0x123
            cycle_time: 100

    float32 speed
        description: "Vehicle speed"
        units: "km/h"
        can_signal:
            min: 0.0
            max: 250.0
            scale: 0.01
            offset: 0.0
        range:
            min: 0.0
            max: 250.0

    uint8 gear
        description: "Current gear"
        range:
            min: 0
            max: 8
```

---

## 3. Attribute Schema Registry

**File: `attributes/registry.py`**

```python
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class AttributeSchema:
    """Schema definition for a set of attributes."""

    def __init__(self, schema_dict: dict):
        self.name = schema_dict['schema_name']
        self.version = schema_dict['version']
        self.description = schema_dict.get('description', '')
        self.field_attributes = schema_dict.get('field_attributes', {})
        self.struct_attributes = schema_dict.get('struct_attributes', {})

    def validate_field_attribute(
        self,
        attr_name: str,
        attr_value: Any
    ) -> ValidationResult:
        """Validate a field attribute against this schema."""
        if attr_name not in self.field_attributes:
            return ValidationResult(
                valid=False,
                error=f"Unknown field attribute '{attr_name}' for schema '{self.name}'"
            )

        spec = self.field_attributes[attr_name]
        return self._validate_value(attr_value, spec)

    def validate_struct_attribute(
        self,
        attr_name: str,
        attr_value: Any
    ) -> ValidationResult:
        """Validate a struct attribute against this schema."""
        if attr_name not in self.struct_attributes:
            return ValidationResult(
                valid=False,
                error=f"Unknown struct attribute '{attr_name}' for schema '{self.name}'"
            )

        spec = self.struct_attributes[attr_name]
        return self._validate_value(attr_value, spec)

    def _validate_value(self, value: Any, spec: dict) -> ValidationResult:
        """Validate value against specification."""
        # Check type
        expected_type = spec['type']
        if not self._check_type(value, expected_type):
            return ValidationResult(
                valid=False,
                error=f"Expected type {expected_type}, got {type(value).__name__}"
            )

        # Check constraints
        if 'constraints' in spec:
            result = self._check_constraints(value, spec['constraints'])
            if not result.valid:
                return result

        # Validate object properties
        if expected_type == 'object':
            return self._validate_object(value, spec.get('properties', {}))

        return ValidationResult(valid=True)

    def _validate_object(self, obj: dict, properties: dict) -> ValidationResult:
        """Validate object properties."""
        for prop_name, prop_spec in properties.items():
            if prop_spec.get('required', False) and prop_name not in obj:
                return ValidationResult(
                    valid=False,
                    error=f"Required property '{prop_name}' missing"
                )

            if prop_name in obj:
                result = self._validate_value(obj[prop_name], prop_spec)
                if not result.valid:
                    return ValidationResult(
                        valid=False,
                        error=f"Property '{prop_name}': {result.error}"
                    )

        return ValidationResult(valid=True)


class AttributeRegistry:
    """Registry of attribute schemas."""

    def __init__(self):
        self.schemas: Dict[str, AttributeSchema] = {}
        self._load_builtin_schemas()

    def _load_builtin_schemas(self):
        """Load built-in attribute schemas."""
        schema_dir = Path(__file__).parent / "config"
        for schema_file in schema_dir.glob("*.yaml"):
            self.load_schema(schema_file)

    def load_schema(self, schema_path: Path):
        """Load an attribute schema from YAML."""
        with open(schema_path) as f:
            schema_dict = yaml.safe_load(f)

        schema = AttributeSchema(schema_dict)
        self.schemas[schema.name] = schema

    def load_schema_from_dict(self, schema_dict: dict):
        """Load schema from dictionary (for user-defined schemas)."""
        schema = AttributeSchema(schema_dict)
        self.schemas[schema.name] = schema

    def get_schema(self, name: str) -> Optional[AttributeSchema]:
        """Get schema by name."""
        return self.schemas.get(name)

    def list_schemas(self) -> List[str]:
        """List all registered schema names."""
        return list(self.schemas.keys())
```

---

## 4. Attribute Validator

**File: `attributes/validator.py`**

```python
class AttributeValidator:
    """Validates attributes against registered schemas."""

    def __init__(self, registry: AttributeRegistry, enabled_schemas: List[str]):
        self.registry = registry
        self.enabled_schemas = enabled_schemas

    def validate_field_attributes(
        self,
        field_info: FieldInfo
    ) -> List[ValidationError]:
        """Validate all attributes on a field."""
        errors = []

        # Combine inline and indented attributes
        all_attrs = {
            **field_info.inline_attributes,
            **field_info.indented_attributes
        }

        for attr_name, attr_value in all_attrs.items():
            # Try to validate against each enabled schema
            validated = False

            for schema_name in self.enabled_schemas:
                schema = self.registry.get_schema(schema_name)
                if schema is None:
                    continue

                # Check if this attribute belongs to this schema
                if attr_name in schema.field_attributes:
                    result = schema.validate_field_attribute(attr_name, attr_value)

                    if not result.valid:
                        errors.append(ValidationError(
                            file_path=field_info.file_path,
                            line=field_info.line_number,
                            column=0,
                            message=f"Invalid attribute '{attr_name}': {result.error}",
                            error_type="invalid_attribute",
                            severity="error"
                        ))

                    validated = True
                    break

            # Warn about unknown attributes (not in any enabled schema)
            if not validated and self.should_warn_unknown():
                errors.append(ValidationError(
                    file_path=field_info.file_path,
                    line=field_info.line_number,
                    column=0,
                    message=f"Unknown attribute '{attr_name}' (not in enabled schemas: {self.enabled_schemas})",
                    error_type="unknown_attribute",
                    severity="warning"
                ))

        return errors

    def validate_struct_attributes(
        self,
        type_info: TypeInfo
    ) -> List[ValidationError]:
        """Validate struct-level attributes."""
        errors = []

        for attr_name, attr_value in type_info.struct_attributes.items():
            validated = False

            for schema_name in self.enabled_schemas:
                schema = self.registry.get_schema(schema_name)
                if schema is None:
                    continue

                if attr_name in schema.struct_attributes:
                    result = schema.validate_struct_attribute(attr_name, attr_value)

                    if not result.valid:
                        errors.append(ValidationError(
                            file_path=type_info.file_path,
                            line=0,
                            column=0,
                            message=f"Invalid struct attribute '{attr_name}': {result.error}",
                            error_type="invalid_attribute",
                            severity="error"
                        ))

                    validated = True
                    break

            if not validated and self.should_warn_unknown():
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=0,
                    column=0,
                    message=f"Unknown struct attribute '{attr_name}'",
                    error_type="unknown_attribute",
                    severity="warning"
                ))

        return errors
```

---

## 5. Configuration

**File: `lumos_idl/config.py` (additions)**

```python
@dataclass
class AttributeConfig:
    """Configuration for attribute system."""

    # Which attribute schemas to enable
    enabled_schemas: List[str] = field(default_factory=lambda: [])

    # User-defined schema files
    custom_schemas: List[Path] = field(default_factory=list)

    # Validation behavior
    warn_unknown_attributes: bool = True
    strict_mode: bool = False  # Fail on unknown attributes

    # Per-schema configuration
    schema_config: Dict[str, dict] = field(default_factory=dict)


@dataclass
class Config:
    # ... existing fields ...

    # Attribute configuration
    attributes: AttributeConfig = field(default_factory=AttributeConfig)
```

**Usage in project config** (`pyproject.toml` or `lumos.toml`):

```toml
[lumos_idl.attributes]
enabled_schemas = ["can_bus", "validation", "ros2"]
warn_unknown_attributes = true
strict_mode = false

# Load custom schemas
custom_schemas = [
    "config/my_custom_attributes.yaml"
]

# CAN bus specific config
[lumos_idl.attributes.can_bus]
default_cycle_time = 100
max_message_id = 0x7FF  # Standard 11-bit CAN
```

---

## 6. Integration into Validator

**File: `validator/validator.py` (additions)**

```python
from ..attributes import AttributeRegistry, AttributeValidator

class IDLValidator:
    def __init__(self, config: Optional[Config] = None):
        # ... existing initialization ...

        # Attribute system
        self.attribute_registry = AttributeRegistry()

        # Load custom schemas
        for schema_path in config.attributes.custom_schemas:
            self.attribute_registry.load_schema(schema_path)

        # Create validator with enabled schemas
        self.attribute_validator = AttributeValidator(
            self.attribute_registry,
            config.attributes.enabled_schemas
        )

    def validate(self, parse_result: ValidationResult) -> ValidationResult:
        # ... existing phases ...

        # Phase 6: Validate attributes
        if self.config.attributes.enabled_schemas:
            for file_path, file_info in parse_result.parsed_files.items():
                self._validate_attributes(file_info)

        # ... rest of validation ...

    def _validate_attributes(self, file_info: FileInfo):
        """Validate attributes against schemas."""
        for type_info in file_info.defined_types:
            # Validate struct attributes
            errors = self.attribute_validator.validate_struct_attributes(type_info)
            for error in errors:
                self.error_reporter.add_error(error)

            # Validate field attributes
            for field in type_info.fields:
                errors = self.attribute_validator.validate_field_attributes(field)
                for error in errors:
                    self.error_reporter.add_error(error)
```

---

## 7. Using Attributes in Code Generators

Code generators can query attributes they care about:

```python
class CanBusGenerator:
    """Generate CAN DBC file from IDL with CAN attributes."""

    def generate_dbc(self, validation_result: ValidationResult) -> str:
        dbc = []

        for file_info in validation_result.parsed_files.values():
            for type_info in file_info.defined_types:
                # Check if this struct is a CAN message
                can_msg_attr = type_info.struct_attributes.get('can_message')
                if not can_msg_attr:
                    continue  # Skip non-CAN structs

                msg_id = can_msg_attr['id']
                cycle_time = can_msg_attr.get('cycle_time', 0)

                dbc.append(f"BO_ {msg_id} {type_info.name}: 8 Vector__XXX")

                # Generate signals from fields
                for field in type_info.fields:
                    can_signal_attr = field.indented_attributes.get('can_signal')
                    if not can_signal_attr:
                        continue  # Skip non-CAN fields

                    min_val = can_signal_attr['min']
                    max_val = can_signal_attr['max']
                    scale = can_signal_attr['scale']
                    offset = can_signal_attr.get('offset', 0.0)
                    unit = can_signal_attr.get('unit', '')

                    dbc.append(f' SG_ {field.name} : ... [{min_val}|{max_val}] "{unit}" ...')

        return '\n'.join(dbc)
```

**Other generators ignore CAN attributes:**

```python
class CppGenerator:
    """C++ generator doesn't care about CAN attributes."""

    def generate_struct(self, type_info: TypeInfo):
        # Generates C++ struct
        # CAN attributes are just ignored - they're not relevant here
        pass
```

---

## 8. Example: Complete Workflow

**1. Define custom attributes** (`my_project/can_config.yaml`):

```yaml
schema_name: my_can_bus
version: "1.0"

field_attributes:
  can_signal:
    type: object
    required: false
    properties:
      min: {type: float, required: true}
      max: {type: float, required: true}
      scale: {type: float, required: true}
      offset: {type: float, default: 0.0}
```

**2. Enable in config** (`my_project/lumos.toml`):

```toml
[lumos_idl.attributes]
enabled_schemas = ["my_can_bus", "validation"]
custom_schemas = ["my_project/can_config.yaml"]
```

**3. Write IDL** (`interfaces/vehicle.msg`):

```
struct VehicleSpeed
    [attributes]
        can_message:
            id: 0x123
            cycle_time: 100

    float32 speed
        description: "Vehicle speed in km/h"
        can_signal:
            min: 0.0
            max: 250.0
            scale: 0.01
        range:
            min: 0.0
            max: 250.0
```

**4. Validate**:

```python
from lumos_idl import IDLProcessor, Config

config = Config.from_file("my_project/lumos.toml")
processor = IDLProcessor(config)

result = processor.process_file("interfaces/vehicle.msg")

if result.success:
    print("✓ Validation passed (including CAN attributes)")
else:
    result.print_errors()
```

**5. Generate code**:

```python
# Generate C++ (ignores CAN attributes)
cpp_gen = CppGenerator(config)
cpp_gen.generate(result, "generated/cpp")

# Generate CAN DBC (uses CAN attributes)
can_gen = CanBusGenerator(config)
dbc_content = can_gen.generate_dbc(result)
Path("generated/vehicle.dbc").write_text(dbc_content)
```

---

## Summary

**Key Design Principles:**

1. ✅ **Grammar stays generic** - supports any key-value attributes
2. ✅ **Schemas are external** - defined in YAML, not hardcoded
3. ✅ **Opt-in validation** - enable only schemas you need
4. ✅ **Generator-specific** - each generator uses relevant attributes
5. ✅ **User-extensible** - easy to add project-specific attributes
6. ✅ **No grammar changes** - add new domains without touching parser

**Benefits:**

- CAN bus attributes don't pollute the IDL grammar
- ROS2 projects can add ROS2 attributes without affecting CAN users
- Custom domains (database, UI, etc.) can define their own schemas
- Validation ensures attributes are used correctly
- Generators pick what they need, ignore the rest

**This gives you maximum flexibility without grammar bloat!**
