"""
LumosInterface IDL - A modern Interface Definition Language.

Usage:
    from lumos_idl import IDLProcessor, Config

    # Simple usage
    processor = IDLProcessor()
    result = processor.parse_file("interfaces/robot_state.msg")

    if result.success:
        print(" Parsing passed")
    else:
        result.print_errors()

    # With configuration
    config = Config.from_file("lumos.toml")
    processor = IDLProcessor(config)
"""

from .config import Config, ValidationConfig, NamingConfig, CodegenConfig
from .parser.ast_parser import ASTParser
from .validator.validator import IDLValidator
from .ast.types import (
    ParseResult,
    ParseError,
    ValidationResult,
    ValidationError,
    FileInfo,
    TypeInfo,
    FieldInfo,
    ConstantInfo,
    AliasInfo,
)
from pathlib import Path
from typing import List, Optional


__version__ = "0.1.0"
__all__ = [
    "IDLProcessor",
    "Config",
    "ParseResult",
    "ValidationResult",
    "ParseError",
    "ValidationError",
    "FileInfo",
    "TypeInfo",
]


class IDLProcessor:
    """
    Main entry point for IDL processing.

    Handles parsing, validation, and code generation.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize IDL processor.

        Args:
            config: Configuration object. If None, uses defaults.
        """
        self.config = config or Config.default()
        self.parser = ASTParser(self.config)
        self.validator = IDLValidator(self.config)

    def parse_file(self, file_path: str) -> ParseResult:
        """
        Parse a single IDL file.

        Args:
            file_path: Path to .msg file

        Returns:
            ParseResult with success status and any errors
        """
        return self.parser.parse_file(file_path)

    def parse_string(self, content: str, file_path: str = "<string>") -> ParseResult:
        """
        Parse IDL content from a string.

        Args:
            content: IDL source code
            file_path: Virtual file path for error reporting

        Returns:
            ParseResult with success status and any errors
        """
        return self.parser.parse_string(content, file_path)

    def parse_files(self, file_paths: List[str]) -> ParseResult:
        """
        Parse multiple IDL files.

        Args:
            file_paths: List of paths to .msg files

        Returns:
            ParseResult with success status and any errors
        """
        combined_result = ParseResult()

        for file_path in file_paths:
            result = self.parser.parse_file(file_path)

            # Merge results
            combined_result.files.update(result.files)
            combined_result.errors.extend(result.errors)
            if not result.success:
                combined_result.success = False

        return combined_result

    def parse_directory(self, directory: str, recursive: bool = True) -> ParseResult:
        """
        Parse all .msg files in a directory.

        Args:
            directory: Directory path
            recursive: Include subdirectories

        Returns:
            ParseResult with success status and any errors
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            result = ParseResult()
            result.add_error(ParseError(
                file_path=dir_path,
                line=0,
                column=0,
                message=f"Directory not found: {directory}",
                error_type="directory_not_found"
            ))
            return result

        if not dir_path.is_dir():
            result = ParseResult()
            result.add_error(ParseError(
                file_path=dir_path,
                line=0,
                column=0,
                message=f"Not a directory: {directory}",
                error_type="not_a_directory"
            ))
            return result

        # Collect all .msg files
        if recursive:
            msg_files = list(dir_path.rglob("*.msg"))
        else:
            msg_files = list(dir_path.glob("*.msg"))

        # Parse all files
        return self.parse_files([str(f) for f in msg_files])

    def process_string(self, content: str, file_path: str = "<string>") -> ValidationResult:
        """
        Parse and validate IDL content from a string.

        Args:
            content: IDL source code
            file_path: Virtual file path for error reporting

        Returns:
            ValidationResult with success status and any errors

        Note:
            Currently only performs parsing. Full validation will be
            implemented in future version.
        """
        parse_result = self.parse_string(content, file_path)

        # Convert ParseResult to ValidationResult
        validation_result = ValidationResult()
        validation_result.parsed_files = parse_result.files
        validation_result.success = parse_result.success

        # Convert ParseErrors to ValidationErrors
        for error in parse_result.errors:
            validation_result.add_error(ValidationError(
                file_path=error.file_path,
                line=error.line,
                column=error.column,
                message=error.message,
                error_type=error.error_type,
                severity="error"
            ))

        # Run semantic validation
        validation_result = self.validator.validate(validation_result)

        return validation_result

    def process_file(self, file_path: str) -> ValidationResult:
        """
        Parse and validate a single IDL file.

        Args:
            file_path: Path to .msg file

        Returns:
            ValidationResult with success status and any errors

        Note:
            Currently only performs parsing. Full validation will be
            implemented in future version.
        """
        parse_result = self.parse_file(file_path)

        # Convert ParseResult to ValidationResult
        validation_result = ValidationResult()
        validation_result.parsed_files = parse_result.files
        validation_result.success = parse_result.success

        # Convert ParseErrors to ValidationErrors
        for error in parse_result.errors:
            validation_result.add_error(ValidationError(
                file_path=error.file_path,
                line=error.line,
                column=error.column,
                message=error.message,
                error_type=error.error_type,
                severity="error"
            ))

        # Run semantic validation
        validation_result = self.validator.validate(validation_result)

        return validation_result

    def process_files(self, file_paths: List[str]) -> ValidationResult:
        """
        Parse and validate multiple IDL files.

        Args:
            file_paths: List of paths to .msg files

        Returns:
            ValidationResult with success status and any errors
        """
        parse_result = self.parse_files(file_paths)

        # Convert ParseResult to ValidationResult
        validation_result = ValidationResult()
        validation_result.parsed_files = parse_result.files
        validation_result.success = parse_result.success

        # Convert ParseErrors to ValidationErrors
        for error in parse_result.errors:
            validation_result.add_error(ValidationError(
                file_path=error.file_path,
                line=error.line,
                column=error.column,
                message=error.message,
                error_type=error.error_type,
                severity="error"
            ))

        # Run semantic validation
        validation_result = self.validator.validate(validation_result)

        return validation_result

    def process_directory(self, directory: str, recursive: bool = True) -> ValidationResult:
        """
        Parse and validate all .msg files in a directory.

        Args:
            directory: Directory path
            recursive: Include subdirectories

        Returns:
            ValidationResult with success status and any errors
        """
        parse_result = self.parse_directory(directory, recursive)

        # Convert ParseResult to ValidationResult
        validation_result = ValidationResult()
        validation_result.parsed_files = parse_result.files
        validation_result.success = parse_result.success

        # Convert ParseErrors to ValidationErrors
        for error in parse_result.errors:
            validation_result.add_error(ValidationError(
                file_path=error.file_path,
                line=error.line,
                column=error.column,
                message=error.message,
                error_type=error.error_type,
                severity="error"
            ))

        # Run semantic validation
        validation_result = self.validator.validate(validation_result)

        return validation_result

    def generate_python(self, result: ValidationResult, output_dir: str):
        """Generate Python code from validated AST."""
        # TODO: Implement code generation
        raise NotImplementedError("Code generation not yet implemented")

    def generate_cpp(self, result: ValidationResult, output_dir: str):
        """Generate C++ code from validated AST."""
        # TODO: Implement code generation
        raise NotImplementedError("Code generation not yet implemented")

    def generate_json_schema(self, result: ValidationResult, output_file: str):
        """Generate JSON schema from validated AST."""
        # TODO: Implement code generation
        raise NotImplementedError("Code generation not yet implemented")
