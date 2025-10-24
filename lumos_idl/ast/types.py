"""
AST type definitions for LumosInterface IDL.

Defines data structures for parsed and validated AST nodes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
from lark import Tree


@dataclass
class FieldInfo:
    """Information about a struct/interface field."""
    name: str
    type_name: str               # Type reference (may be unresolved initially)
    field_number: Optional[int] = None  # Field number (if specified)
    optional: bool = False
    inline_attributes: Dict[str, Any] = field(default_factory=dict)
    indented_attributes: Dict[str, Any] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class EnumMemberInfo:
    """Information about an enum member."""
    name: str
    value: int                   # Actual integer value (after auto-increment resolution)
    line_number: int = 0


@dataclass
class TypeInfo:
    """Information about a defined type."""
    name: str                    # Simple name (e.g., "Position")
    qualified_name: str          # Full name (e.g., "common::geometry::Position")
    kind: str                    # "struct", "interface", "enum"
    file_path: Path              # Where it's defined
    ast_node: Tree               # AST node reference
    fields: List[FieldInfo] = field(default_factory=list)               # For struct/interface
    enum_members: List[EnumMemberInfo] = field(default_factory=list)    # For enum
    enum_storage_type: str = "int32"  # Storage type for enum (default: int32)
    struct_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstantInfo:
    """Information about a constant definition."""
    name: str
    type_name: str
    value: Any
    qualified_name: str
    file_path: Path
    line_number: int = 0


@dataclass
class AliasInfo:
    """Information about a type alias."""
    name: str
    target_type: str
    qualified_name: str
    file_path: Path
    line_number: int = 0


@dataclass
class FileInfo:
    """Information about a parsed file."""
    path: Path
    namespace: str               # Derived from path (e.g., "common::geometry")
    imports: List[str] = field(default_factory=list)           # Import paths
    using_namespaces: List[str] = field(default_factory=list)  # "using namespace X" statements
    namespace_aliases: Dict[str, str] = field(default_factory=dict)  # "namespace x = y" statements
    defined_types: List[TypeInfo] = field(default_factory=list)      # Types defined in this file
    defined_constants: List[ConstantInfo] = field(default_factory=list)  # Constants defined
    defined_aliases: List[AliasInfo] = field(default_factory=list)       # Type aliases defined
    ast: Optional[Tree] = None   # Parsed AST


@dataclass
class ParseError:
    """Information about a parsing error."""
    file_path: Path
    line: int
    column: int
    message: str
    error_type: str = "parse_error"

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line}:{self.column}: {self.error_type}: {self.message}"


@dataclass
class ValidationError:
    """Information about a validation error."""
    file_path: Path
    line: int
    column: int
    message: str
    error_type: str  # "type_not_found", "circular_import", "duplicate_field_number", etc.
    severity: str = "error"  # "error", "warning", "info"

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line}:{self.column}: {self.severity}: {self.error_type}: {self.message}"


@dataclass
class ParseResult:
    """Result of parsing operation."""
    files: Dict[Path, FileInfo] = field(default_factory=dict)
    errors: List[ParseError] = field(default_factory=list)
    success: bool = True

    def add_error(self, error: ParseError):
        """Add a parse error."""
        self.errors.append(error)
        self.success = False


@dataclass
class ValidationResult:
    """Result of validation operation."""
    parsed_files: Dict[Path, FileInfo] = field(default_factory=dict)
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    success: bool = True

    def add_error(self, error: ValidationError):
        """Add a validation error."""
        if error.severity == "error":
            self.errors.append(error)
            self.success = False
        elif error.severity == "warning":
            self.warnings.append(error)

    def print_errors(self):
        """Print formatted errors and warnings."""
        if self.errors:
            print(f"\n{len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n{len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  {warning}")

    def get_all_types(self) -> Dict[str, TypeInfo]:
        """Get all defined types across all files."""
        all_types = {}
        for file_info in self.parsed_files.values():
            for type_info in file_info.defined_types:
                all_types[type_info.qualified_name] = type_info
        return all_types
