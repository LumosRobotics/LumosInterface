"""
Attribute schema registry for LumosInterface IDL.

Manages attribute schemas and provides validation capabilities.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml


@dataclass
class ValidationResult:
    """Result of attribute validation."""
    valid: bool
    error: Optional[str] = None


class AttributeSchema:
    """Schema definition for a set of attributes."""

    def __init__(self, schema_dict: dict):
        """
        Initialize attribute schema from dictionary.

        Args:
            schema_dict: Schema definition loaded from YAML
        """
        self.name = schema_dict['schema_name']
        self.version = schema_dict.get('version', '1.0')
        self.description = schema_dict.get('description', '')
        self.field_attributes = schema_dict.get('field_attributes', {})
        self.struct_attributes = schema_dict.get('struct_attributes', {})
        self.enum_attributes = schema_dict.get('enum_attributes', {})

    def validate_field_attribute(
        self,
        attr_name: str,
        attr_value: Any
    ) -> ValidationResult:
        """
        Validate a field attribute against this schema.

        Args:
            attr_name: Name of the attribute
            attr_value: Value of the attribute

        Returns:
            ValidationResult indicating success or failure
        """
        if attr_name not in self.field_attributes:
            return ValidationResult(
                valid=False,
                error=f"Unknown field attribute '{attr_name}' for schema '{self.name}'"
            )

        spec = self.field_attributes[attr_name]
        return self._validate_value(attr_value, spec, attr_name)

    def validate_struct_attribute(
        self,
        attr_name: str,
        attr_value: Any
    ) -> ValidationResult:
        """
        Validate a struct attribute against this schema.

        Args:
            attr_name: Name of the attribute
            attr_value: Value of the attribute

        Returns:
            ValidationResult indicating success or failure
        """
        if attr_name not in self.struct_attributes:
            return ValidationResult(
                valid=False,
                error=f"Unknown struct attribute '{attr_name}' for schema '{self.name}'"
            )

        spec = self.struct_attributes[attr_name]
        return self._validate_value(attr_value, spec, attr_name)

    def validate_enum_attribute(
        self,
        attr_name: str,
        attr_value: Any
    ) -> ValidationResult:
        """
        Validate an enum attribute against this schema.

        Args:
            attr_name: Name of the attribute
            attr_value: Value of the attribute

        Returns:
            ValidationResult indicating success or failure
        """
        if attr_name not in self.enum_attributes:
            return ValidationResult(
                valid=False,
                error=f"Unknown enum attribute '{attr_name}' for schema '{self.name}'"
            )

        spec = self.enum_attributes[attr_name]
        return self._validate_value(attr_value, spec, attr_name)

    def _validate_value(self, value: Any, spec: dict, attr_name: str) -> ValidationResult:
        """
        Validate value against specification.

        Args:
            value: Value to validate
            spec: Specification from schema
            attr_name: Name of attribute (for error messages)

        Returns:
            ValidationResult
        """
        # Check type
        expected_type = spec.get('type')
        if expected_type is None:
            return ValidationResult(
                valid=False,
                error=f"Schema error: no type specified for '{attr_name}'"
            )

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

        # Validate array items
        if expected_type == 'array':
            return self._validate_array(value, spec)

        return ValidationResult(valid=True)

    def _check_type(self, value: Any, expected_type: Union[str, List[str]]) -> bool:
        """
        Check if value matches expected type.

        Args:
            value: Value to check
            expected_type: Expected type(s) - can be string or list of strings

        Returns:
            True if type matches
        """
        # Handle multiple allowed types
        if isinstance(expected_type, list):
            return any(self._check_type(value, t) for t in expected_type)

        type_map = {
            'string': str,
            'integer': int,
            'float': (int, float),  # Allow int for float
            'number': (int, float),
            'boolean': bool,
            'object': dict,
            'array': list,
        }

        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return False

        return isinstance(value, expected_python_type)

    def _check_constraints(self, value: Any, constraints: dict) -> ValidationResult:
        """
        Check value against constraints.

        Args:
            value: Value to check
            constraints: Constraint specifications

        Returns:
            ValidationResult
        """
        # Min/max for numbers
        if isinstance(value, (int, float)):
            if 'min' in constraints and value < constraints['min']:
                return ValidationResult(
                    valid=False,
                    error=f"Value {value} is less than minimum {constraints['min']}"
                )
            if 'max' in constraints and value > constraints['max']:
                return ValidationResult(
                    valid=False,
                    error=f"Value {value} is greater than maximum {constraints['max']}"
                )

        # Min/max length for strings and arrays
        if isinstance(value, (str, list)):
            if 'min_length' in constraints and len(value) < constraints['min_length']:
                return ValidationResult(
                    valid=False,
                    error=f"Length {len(value)} is less than minimum {constraints['min_length']}"
                )
            if 'max_length' in constraints and len(value) > constraints['max_length']:
                return ValidationResult(
                    valid=False,
                    error=f"Length {len(value)} is greater than maximum {constraints['max_length']}"
                )

        # Pattern matching for strings
        if isinstance(value, str) and 'pattern' in constraints:
            import re
            pattern = constraints['pattern']
            if not re.match(pattern, value):
                return ValidationResult(
                    valid=False,
                    error=f"Value '{value}' does not match pattern '{pattern}'"
                )

        # Enum values
        if 'enum' in constraints:
            if value not in constraints['enum']:
                return ValidationResult(
                    valid=False,
                    error=f"Value '{value}' not in allowed values: {constraints['enum']}"
                )

        return ValidationResult(valid=True)

    def _validate_object(self, obj: dict, properties: dict) -> ValidationResult:
        """
        Validate object properties.

        Args:
            obj: Object to validate (dictionary)
            properties: Property specifications

        Returns:
            ValidationResult
        """
        # Check required properties
        for prop_name, prop_spec in properties.items():
            if prop_spec.get('required', False) and prop_name not in obj:
                return ValidationResult(
                    valid=False,
                    error=f"Required property '{prop_name}' missing"
                )

        # Validate each present property
        for prop_name, prop_value in obj.items():
            if prop_name not in properties:
                # Unknown property - could warn here
                continue

            prop_spec = properties[prop_name]
            result = self._validate_value(prop_value, prop_spec, prop_name)
            if not result.valid:
                return ValidationResult(
                    valid=False,
                    error=f"Property '{prop_name}': {result.error}"
                )

        return ValidationResult(valid=True)

    def _validate_array(self, arr: list, spec: dict) -> ValidationResult:
        """
        Validate array items.

        Args:
            arr: Array to validate
            spec: Array specification

        Returns:
            ValidationResult
        """
        if 'items' not in spec:
            return ValidationResult(valid=True)

        item_spec = spec['items']
        for i, item in enumerate(arr):
            result = self._validate_value(item, item_spec, f"item[{i}]")
            if not result.valid:
                return ValidationResult(
                    valid=False,
                    error=f"Array item {i}: {result.error}"
                )

        return ValidationResult(valid=True)


class AttributeRegistry:
    """Registry of attribute schemas."""

    def __init__(self):
        """Initialize attribute registry."""
        self.schemas: Dict[str, AttributeSchema] = {}

    def load_builtin_schemas(self):
        """Load built-in attribute schemas from config directory."""
        schema_dir = Path(__file__).parent / "config"
        if not schema_dir.exists():
            return

        for schema_file in schema_dir.glob("*.yaml"):
            try:
                self.load_schema(schema_file)
            except Exception as e:
                # Silently skip invalid schemas
                # In production, you might want to log this
                pass

    def load_schema(self, schema_path: Path):
        """
        Load an attribute schema from YAML file.

        Args:
            schema_path: Path to YAML schema file
        """
        with open(schema_path, 'r') as f:
            schema_dict = yaml.safe_load(f)

        schema = AttributeSchema(schema_dict)
        self.schemas[schema.name] = schema

    def load_schema_from_dict(self, schema_dict: dict):
        """
        Load schema from dictionary (for user-defined schemas).

        Args:
            schema_dict: Schema definition as dictionary
        """
        schema = AttributeSchema(schema_dict)
        self.schemas[schema.name] = schema

    def get_schema(self, name: str) -> Optional[AttributeSchema]:
        """
        Get schema by name.

        Args:
            name: Schema name

        Returns:
            AttributeSchema if found, None otherwise
        """
        return self.schemas.get(name)

    def list_schemas(self) -> List[str]:
        """
        List all registered schema names.

        Returns:
            List of schema names
        """
        return list(self.schemas.keys())

    def has_schema(self, name: str) -> bool:
        """
        Check if a schema is registered.

        Args:
            name: Schema name

        Returns:
            True if schema exists
        """
        return name in self.schemas
