"""
Enum validator for LumosInterface IDL.

Validates enum definitions and member constraints.
"""

from typing import List, Dict, Set
from ..ast.types import TypeInfo, ValidationError, EnumMemberInfo
from ..config import Config


class EnumValidator:
    """Validates enum definitions and members."""

    def __init__(self, config: Config):
        """
        Initialize enum validator.

        Args:
            config: Configuration object
        """
        self.config = config

        # Type ranges for validation
        self.type_ranges = {
            "int8": (-128, 127),
            "int16": (-32768, 32767),
            "int32": (-2147483648, 2147483647),
            "int64": (-9223372036854775808, 9223372036854775807),
            "uint8": (0, 255),
            "uint16": (0, 65535),
            "uint32": (0, 4294967295),
            "uint64": (0, 18446744073709551615),
        }

        # Valid storage types for enums
        self.valid_storage_types = set(self.type_ranges.keys())

    def validate_enum(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate an enum definition.

        Args:
            type_info: TypeInfo for the enum to validate

        Returns:
            List of validation errors
        """
        if type_info.kind != "enum":
            return []

        errors = []

        # Validate storage type
        errors.extend(self._validate_storage_type(type_info))

        # Validate that enum has at least one member
        errors.extend(self._validate_has_members(type_info))

        # Validate member names are unique
        errors.extend(self._validate_unique_names(type_info))

        # Validate member values are unique
        errors.extend(self._validate_unique_values(type_info))

        # Validate member values fit in storage type
        errors.extend(self._validate_value_ranges(type_info))

        return errors

    def _validate_storage_type(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate that the storage type is valid for enums.

        Args:
            type_info: TypeInfo for the enum

        Returns:
            List of validation errors
        """
        errors = []

        storage_type = type_info.enum_storage_type

        if storage_type not in self.valid_storage_types:
            errors.append(ValidationError(
                file_path=type_info.file_path,
                line=0,  # TODO: Get actual line number from AST
                column=0,
                message=f"Invalid storage type '{storage_type}' for enum '{type_info.name}'. "
                       f"Must be an integer type (int8/16/32/64 or uint8/16/32/64).",
                error_type="invalid_enum_storage_type",
                severity="error"
            ))

        return errors

    def _validate_has_members(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate that the enum has at least one member.

        Args:
            type_info: TypeInfo for the enum

        Returns:
            List of validation errors
        """
        errors = []

        if len(type_info.enum_members) == 0:
            errors.append(ValidationError(
                file_path=type_info.file_path,
                line=0,
                column=0,
                message=f"Enum '{type_info.name}' must have at least one member.",
                error_type="empty_enum",
                severity="error"
            ))

        return errors

    def _validate_unique_names(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate that all enum member names are unique.

        Args:
            type_info: TypeInfo for the enum

        Returns:
            List of validation errors
        """
        errors = []

        name_to_members: Dict[str, List[EnumMemberInfo]] = {}

        for member in type_info.enum_members:
            if member.name not in name_to_members:
                name_to_members[member.name] = []
            name_to_members[member.name].append(member)

        # Check for duplicates
        for name, members in name_to_members.items():
            if len(members) > 1:
                member_list = ", ".join([f"'{m.name}'" for m in members])
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=members[1].line_number,  # Report on second occurrence
                    column=0,
                    message=f"Duplicate enum member name '{name}' in enum '{type_info.name}'. "
                           f"Member names must be unique.",
                    error_type="duplicate_enum_member_name",
                    severity="error"
                ))

        return errors

    def _validate_unique_values(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate that all enum member values are unique (no aliasing).

        Args:
            type_info: TypeInfo for the enum

        Returns:
            List of validation errors
        """
        errors = []

        value_to_members: Dict[int, List[EnumMemberInfo]] = {}

        for member in type_info.enum_members:
            if member.value not in value_to_members:
                value_to_members[member.value] = []
            value_to_members[member.value].append(member)

        # Check for duplicates
        for value, members in value_to_members.items():
            if len(members) > 1:
                member_names = ", ".join([f"'{m.name}'" for m in members])
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=members[1].line_number,  # Report on second occurrence
                    column=0,
                    message=f"Duplicate enum value {value} in enum '{type_info.name}'. "
                           f"Members {member_names} have the same value. "
                           f"Enum values must be unique.",
                    error_type="duplicate_enum_value",
                    severity="error"
                ))

        return errors

    def _validate_value_ranges(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate that all enum values fit in the storage type.

        Args:
            type_info: TypeInfo for the enum

        Returns:
            List of validation errors
        """
        errors = []

        storage_type = type_info.enum_storage_type

        # Get range for storage type
        if storage_type not in self.type_ranges:
            # Invalid storage type - will be caught by _validate_storage_type
            return errors

        min_value, max_value = self.type_ranges[storage_type]

        # Check each member value
        for member in type_info.enum_members:
            if member.value < min_value or member.value > max_value:
                errors.append(ValidationError(
                    file_path=type_info.file_path,
                    line=member.line_number,
                    column=0,
                    message=f"Enum member '{member.name}' has value {member.value} which is out of range "
                           f"for storage type '{storage_type}' (range: {min_value} to {max_value}).",
                    error_type="enum_value_out_of_range",
                    severity="error"
                ))

        return errors
