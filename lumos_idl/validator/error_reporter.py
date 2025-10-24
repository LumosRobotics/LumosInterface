"""
Error reporter for LumosInterface IDL validation.

Collects and formats validation errors and warnings.
"""

from typing import List
from pathlib import Path
from ..ast.types import ValidationError


class ErrorReporter:
    """Collects and formats validation errors."""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(self, error: ValidationError):
        """
        Add an error.

        Args:
            error: ValidationError to add
        """
        if error.severity == "error":
            self.errors.append(error)
        elif error.severity == "warning":
            self.warnings.append(error)
        elif error.severity == "info":
            # Info messages go to warnings for now
            self.warnings.append(error)

    def add_warning(self, warning: ValidationError):
        """
        Add a warning.

        Args:
            warning: ValidationError with severity="warning"
        """
        warning.severity = "warning"
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """
        Check if any errors were reported.

        Returns:
            True if errors exist, False otherwise
        """
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """
        Check if any warnings were reported.

        Returns:
            True if warnings exist, False otherwise
        """
        return len(self.warnings) > 0

    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)

    def warning_count(self) -> int:
        """Get number of warnings."""
        return len(self.warnings)

    def clear(self):
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()

    def format_report(self, show_warnings: bool = True) -> str:
        """
        Format errors and warnings for display.

        Args:
            show_warnings: Include warnings in output

        Returns:
            Formatted string with all errors and warnings

        Format:
            Error: type_not_found
              File: common/geometry.msg:15:5
              Message: Type 'Vector4' not found

            Warning: field_number_gap
              File: data.msg:23:5
              Message: Field number gap detected (1 -> 5). Consider reserving 2-4.
        """
        lines = []

        if self.errors:
            lines.append(f"\n{len(self.errors)} error(s):")
            for error in self.errors:
                lines.append(self._format_error(error))

        if show_warnings and self.warnings:
            lines.append(f"\n{len(self.warnings)} warning(s):")
            for warning in self.warnings:
                lines.append(self._format_error(warning))

        return "\n".join(lines)

    def _format_error(self, error: ValidationError) -> str:
        """
        Format a single error/warning.

        Args:
            error: ValidationError to format

        Returns:
            Formatted error string
        """
        severity_label = error.severity.capitalize()
        location = f"{error.file_path}:{error.line}:{error.column}"

        lines = [
            f"  {severity_label}: {error.error_type}",
            f"    Location: {location}",
            f"    Message: {error.message}",
        ]

        return "\n".join(lines)

    def print_report(self, show_warnings: bool = True):
        """
        Print formatted report to stdout.

        Args:
            show_warnings: Include warnings in output
        """
        report = self.format_report(show_warnings)
        if report:
            print(report)

    def get_errors_by_file(self) -> dict:
        """
        Get errors grouped by file.

        Returns:
            Dictionary mapping file paths to lists of errors
        """
        errors_by_file = {}
        for error in self.errors:
            if error.file_path not in errors_by_file:
                errors_by_file[error.file_path] = []
            errors_by_file[error.file_path].append(error)
        return errors_by_file

    def get_warnings_by_file(self) -> dict:
        """
        Get warnings grouped by file.

        Returns:
            Dictionary mapping file paths to lists of warnings
        """
        warnings_by_file = {}
        for warning in self.warnings:
            if warning.file_path not in warnings_by_file:
                warnings_by_file[warning.file_path] = []
            warnings_by_file[warning.file_path].append(warning)
        return warnings_by_file

    def get_errors_by_type(self) -> dict:
        """
        Get errors grouped by error type.

        Returns:
            Dictionary mapping error types to lists of errors
        """
        errors_by_type = {}
        for error in self.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)
        return errors_by_type

    def summary(self) -> str:
        """
        Get a brief summary of errors and warnings.

        Returns:
            Summary string
        """
        if not self.has_errors() and not self.has_warnings():
            return "No errors or warnings"

        parts = []
        if self.has_errors():
            parts.append(f"{self.error_count()} error(s)")
        if self.has_warnings():
            parts.append(f"{self.warning_count()} warning(s)")

        return ", ".join(parts)
