"""
Field validator for LumosInterface IDL.

Validates field-specific rules including numbering, naming, and constraints.
"""

from typing import List, Dict, Set, Optional
from ..ast.types import TypeInfo, FieldInfo, ValidationError
from ..config import Config


class FieldValidator:
    """Validates struct/interface field constraints."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize field validator.

        Args:
            config: Configuration object
        """
        self.config = config or Config.default()

    def validate_type(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate all field rules for a type.

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of ValidationErrors
        """
        errors = []

        # Validate field numbering
        errors.extend(self.validate_field_numbering(type_info))

        # Validate field names
        errors.extend(self.validate_field_names(type_info))

        # Validate optional fields
        errors.extend(self.validate_optional_fields(type_info))

        return errors

    def validate_field_numbering(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate field numbering rules:
        1. All-or-nothing: if any field has number, all must have numbers
        2. Uniqueness: no duplicate numbers within struct
        3. Range: warn if negative or > max_field_number
        4. Gaps: warn about gaps in field numbers

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of ValidationErrors
        """
        errors = []

        if not type_info.fields:
            return errors

        # Count fields with and without numbers
        fields_with_numbers = [f for f in type_info.fields if f.field_number is not None]
        fields_without_numbers = [f for f in type_info.fields if f.field_number is None]

        # Rule 1: All-or-nothing
        if fields_with_numbers and fields_without_numbers:
            # Some have numbers, some don't - error
            errors.append(ValidationError(
                file_path=type_info.file_path,
                line=fields_without_numbers[0].line_number,
                column=0,
                message=(
                    f"Field '{fields_without_numbers[0].name}' is missing a field number. "
                    f"In type '{type_info.name}', if any field has a number, all fields must have numbers."
                ),
                error_type="field_numbering_inconsistent",
                severity="error"
            ))
            # Don't continue with other numbering checks if this rule fails
            return errors

        # If no fields have numbers, that's ok (numbering is optional)
        if not fields_with_numbers:
            return errors

        # From here on, all fields have numbers

        # Rule 2: Uniqueness
        number_to_fields: Dict[int, List[FieldInfo]] = {}
        for field in fields_with_numbers:
            num = field.field_number
            if num not in number_to_fields:
                number_to_fields[num] = []
            number_to_fields[num].append(field)

        for num, fields in number_to_fields.items():
            if len(fields) > 1:
                # Duplicate field number
                field_names = ", ".join([f"'{f.name}'" for f in fields])
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=fields[0].line_number,
                    column=0,
                    message=(
                        f"Duplicate field number {num} in type '{type_info.name}'. "
                        f"Fields {field_names} have the same number."
                    ),
                    error_type="duplicate_field_number",
                    severity="error"
                ))

        # Rule 3: Range validation
        for field in fields_with_numbers:
            num = field.field_number

            # Check for negative numbers (if not allowed by config)
            if not self.config.validation.allow_negative_field_numbers and num < 0:
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=field.line_number,
                    column=0,
                    message=(
                        f"Field '{field.name}' has negative field number {num}. "
                        f"Negative field numbers are not allowed."
                    ),
                    error_type="negative_field_number",
                    severity="error"
                ))

            # Check for numbers exceeding max (protobuf limit by default)
            if num > self.config.validation.max_field_number:
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=field.line_number,
                    column=0,
                    message=(
                        f"Field '{field.name}' has field number {num} which exceeds "
                        f"maximum allowed value {self.config.validation.max_field_number}."
                    ),
                    error_type="field_number_too_large",
                    severity="error"
                ))

        # Rule 4: Gap detection (warning only)
        if self.config.validation.warn_on_number_gaps and len(fields_with_numbers) > 1:
            # Sort field numbers
            sorted_numbers = sorted([f.field_number for f in fields_with_numbers])

            # Check for gaps
            for i in range(len(sorted_numbers) - 1):
                current = sorted_numbers[i]
                next_num = sorted_numbers[i + 1]
                gap = next_num - current - 1

                if gap > 0:
                    # There's a gap
                    gap_start = current + 1
                    gap_end = next_num - 1

                    if gap == 1:
                        gap_desc = str(gap_start)
                    else:
                        gap_desc = f"{gap_start}-{gap_end}"

                    errors.append(ValidationError(
                        file_path=type_info.file_path,
                        line=type_info.fields[0].line_number,
                        column=0,
                        message=(
                            f"Field number gap detected in type '{type_info.name}': "
                            f"numbers jump from {current} to {next_num} (missing {gap_desc}). "
                            f"Consider reserving these numbers for future use."
                        ),
                        error_type="field_number_gap",
                        severity="warning"
                    ))

        return errors

    def validate_field_names(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate field name rules:
        1. Uniqueness: no duplicate field names
        2. Naming convention: optional warnings based on config

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of ValidationErrors
        """
        errors = []

        if not type_info.fields:
            return errors

        # Rule 1: Uniqueness
        name_to_fields: Dict[str, List[FieldInfo]] = {}
        for field in type_info.fields:
            name = field.name
            if name not in name_to_fields:
                name_to_fields[name] = []
            name_to_fields[name].append(field)

        for name, fields in name_to_fields.items():
            if len(fields) > 1:
                # Duplicate field name
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=fields[1].line_number,  # Second occurrence
                    column=0,
                    message=(
                        f"Duplicate field name '{name}' in type '{type_info.name}'. "
                        f"Field names must be unique within a type."
                    ),
                    error_type="duplicate_field_name",
                    severity="error"
                ))

        # Rule 2: Naming convention (if enabled)
        if self.config.validation.enforce_naming_conventions:
            import re
            pattern = self.config.naming.field_name_pattern

            for field in type_info.fields:
                if not re.match(pattern, field.name):
                    errors.append(ValidationError(
                        file_path=type_info.file_path,
                        line=field.line_number,
                        column=0,
                        message=(
                            f"Field name '{field.name}' does not match naming convention. "
                            f"Expected pattern: {pattern}"
                        ),
                        error_type="invalid_field_name",
                        severity="warning"
                    ))

        return errors

    def validate_optional_fields(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate optional field usage.

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of ValidationErrors
        """
        errors = []

        # For now, optional fields are always valid
        # Future rules could include:
        # - Optional fields should have field numbers (for serialization)
        # - Optional fields with complex types need special handling
        # - etc.

        return errors

    def validate_collection_sizes(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate collection size constraints:
        1. Fixed size > 0
        2. Max size > 0
        3. Matrix must have exactly 2 dimensions
        4. Tensor must have at least 1 dimension

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of ValidationErrors

        Note:
            Full implementation requires parsing collection type details from AST.
            This is a placeholder for future implementation.
        """
        errors = []

        # TODO: Implement collection validation
        # This requires extracting collection type details from the AST
        # which wasn't done in the basic field extraction

        return errors

    def validate_attributes(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate field attributes:
        1. Valid attribute names (if restricted)
        2. Valid attribute values
        3. Conflicting attributes

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of ValidationErrors

        Note:
            Attribute validation depends on having a schema of valid attributes.
            This is a placeholder for future implementation.
        """
        errors = []

        # TODO: Implement attribute validation
        # This requires defining a schema of valid attributes
        # and their expected value types

        return errors
