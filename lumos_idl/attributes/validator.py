"""
Attribute validator for LumosInterface IDL.

Validates attributes against registered schemas.
"""

from typing import List
from ..ast.types import FieldInfo, TypeInfo, ValidationError
from .registry import AttributeRegistry


class AttributeValidator:
    """Validates attributes against registered schemas."""

    def __init__(
        self,
        registry: AttributeRegistry,
        enabled_schemas: List[str],
        warn_unknown: bool = True
    ):
        """
        Initialize attribute validator.

        Args:
            registry: Attribute registry with loaded schemas
            enabled_schemas: List of schema names to validate against
            warn_unknown: Whether to warn about unknown attributes
        """
        self.registry = registry
        self.enabled_schemas = enabled_schemas
        self.warn_unknown = warn_unknown

    def validate_field_attributes(
        self,
        field_info: FieldInfo
    ) -> List[ValidationError]:
        """
        Validate all attributes on a field.

        Args:
            field_info: Field to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Combine inline and indented attributes
        all_attrs = {
            **field_info.inline_attributes,
            **field_info.indented_attributes
        }

        for attr_name, attr_value in all_attrs.items():
            # Try to validate against each enabled schema
            validated = False
            validation_errors = []

            for schema_name in self.enabled_schemas:
                schema = self.registry.get_schema(schema_name)
                if schema is None:
                    # Schema not found - might want to warn
                    continue

                # Check if this attribute belongs to this schema
                if attr_name in schema.field_attributes:
                    result = schema.validate_field_attribute(attr_name, attr_value)

                    if not result.valid:
                        validation_errors.append((schema_name, result.error))
                    else:
                        # Valid in this schema
                        validated = True
                        validation_errors.clear()
                        break

            # Report validation errors
            if validation_errors:
                for schema_name, error_msg in validation_errors:
                    errors.append(ValidationError(
                        file_path=field_info.file_path,
                        line=field_info.line_number,
                        column=0,
                        message=f"Invalid attribute '{attr_name}' (schema '{schema_name}'): {error_msg}",
                        error_type="invalid_attribute",
                        severity="error"
                    ))

            # Warn about unknown attributes (not in any enabled schema)
            if not validated and self.warn_unknown and not validation_errors:
                errors.append(ValidationError(
                    file_path=field_info.file_path,
                    line=field_info.line_number,
                    column=0,
                    message=f"Unknown attribute '{attr_name}' (not in enabled schemas: {', '.join(self.enabled_schemas)})",
                    error_type="unknown_attribute",
                    severity="warning"
                ))

        return errors

    def validate_struct_attributes(
        self,
        type_info: TypeInfo
    ) -> List[ValidationError]:
        """
        Validate struct-level attributes.

        Args:
            type_info: Struct type to validate

        Returns:
            List of validation errors
        """
        errors = []

        for attr_name, attr_value in type_info.struct_attributes.items():
            validated = False
            validation_errors = []

            for schema_name in self.enabled_schemas:
                schema = self.registry.get_schema(schema_name)
                if schema is None:
                    continue

                if attr_name in schema.struct_attributes:
                    result = schema.validate_struct_attribute(attr_name, attr_value)

                    if not result.valid:
                        validation_errors.append((schema_name, result.error))
                    else:
                        validated = True
                        validation_errors.clear()
                        break

            # Report validation errors
            if validation_errors:
                for schema_name, error_msg in validation_errors:
                    errors.append(ValidationError(
                        file_path=type_info.file_path,
                        line=0,
                        column=0,
                        message=f"Invalid struct attribute '{attr_name}' (schema '{schema_name}'): {error_msg}",
                        error_type="invalid_attribute",
                        severity="error"
                    ))

            if not validated and self.warn_unknown and not validation_errors:
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=0,
                    column=0,
                    message=f"Unknown struct attribute '{attr_name}' (not in enabled schemas: {', '.join(self.enabled_schemas)})",
                    error_type="unknown_attribute",
                    severity="warning"
                ))

        return errors

    def validate_enum_attributes(
        self,
        type_info: TypeInfo
    ) -> List[ValidationError]:
        """
        Validate enum-level attributes.

        Args:
            type_info: Enum type to validate

        Returns:
            List of validation errors
        """
        errors = []

        for attr_name, attr_value in type_info.struct_attributes.items():
            validated = False
            validation_errors = []

            for schema_name in self.enabled_schemas:
                schema = self.registry.get_schema(schema_name)
                if schema is None:
                    continue

                if attr_name in schema.enum_attributes:
                    result = schema.validate_enum_attribute(attr_name, attr_value)

                    if not result.valid:
                        validation_errors.append((schema_name, result.error))
                    else:
                        validated = True
                        validation_errors.clear()
                        break

            # Report validation errors
            if validation_errors:
                for schema_name, error_msg in validation_errors:
                    errors.append(ValidationError(
                        file_path=type_info.file_path,
                        line=0,
                        column=0,
                        message=f"Invalid enum attribute '{attr_name}' (schema '{schema_name}'): {error_msg}",
                        error_type="invalid_attribute",
                        severity="error"
                    ))

            if not validated and self.warn_unknown and not validation_errors:
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=0,
                    column=0,
                    message=f"Unknown enum attribute '{attr_name}' (not in enabled schemas: {', '.join(self.enabled_schemas)})",
                    error_type="unknown_attribute",
                    severity="warning"
                ))

        return errors
