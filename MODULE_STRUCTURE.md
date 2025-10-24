# LumosInterface Python Module Structure

## Overview

This document defines the structure of the `lumos_idl` Python module - a single entry point for parsing, validating, and processing LumosInterface IDL files.

---

## Directory Structure

```
LumosInterface/
├── lumos_idl/                      # Main Python package
│   ├── __init__.py                 # Package entry point, public API
│   ├── config.py                   # Configuration management
│   ├── parser/                     # Parsing phase
│   │   ├── __init__.py
│   │   ├── grammar_loader.py      # Load and cache grammar
│   │   ├── preprocessor.py        # Indentation preprocessing
│   │   └── ast_parser.py          # AST parsing with Lark
│   ├── validator/                  # Validation phase
│   │   ├── __init__.py
│   │   ├── symbol_table.py        # Symbol table management
│   │   ├── import_resolver.py     # Import resolution
│   │   ├── type_checker.py        # Type validation
│   │   ├── field_validator.py     # Field validation
│   │   └── error_reporter.py      # Error reporting
│   ├── ast/                        # AST utilities
│   │   ├── __init__.py
│   │   ├── visitor.py             # AST visitor pattern
│   │   ├── transformer.py         # AST transformation
│   │   └── types.py               # Type definitions for AST nodes
│   ├── codegen/                    # Code generation (future)
│   │   ├── __init__.py
│   │   ├── python.py              # Python code generator
│   │   ├── cpp.py                 # C++ code generator
│   │   └── json_schema.py         # JSON schema generator
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── path_utils.py          # Path resolution utilities
│       └── namespace_utils.py     # Namespace utilities
├── grammar/                        # Grammar files
│   └── message.lark
├── examples/                       # Example IDL files
│   ├── simple.msg
│   └── robot_state.msg
├── tests/                          # Test suite
│   ├── test_parser.py
│   ├── test_validator.py
│   └── test_files/
├── pyproject.toml                  # Modern Python project config
├── setup.py                        # Legacy setup (for compatibility)
├── README.md                       # Documentation
└── lumos.toml                      # Default configuration file
```

---

## Public API (`lumos_idl/__init__.py`)

### Main Entry Point

```python
"""
LumosInterface IDL - A modern Interface Definition Language.

Usage:
    from lumos_idl import IDLProcessor, Config

    # Simple usage
    processor = IDLProcessor()
    result = processor.process_file("interfaces/robot_state.msg")

    # With configuration
    config = Config.from_file("lumos.toml")
    processor = IDLProcessor(config)
    result = processor.process_files([
        "interfaces/robot_state.msg",
        "interfaces/sensor_data.msg"
    ])

    if result.success:
        print("✓ Validation passed")
        # Generate code
        processor.generate_python(result, output_dir="generated/")
    else:
        result.print_errors()
"""

from .config import Config, SearchPath
from .parser.ast_parser import ASTParser
from .validator.validator import IDLValidator
from .ast.types import ParsedFile, ValidationResult

__version__ = "0.1.0"
__all__ = [
    "IDLProcessor",
    "Config",
    "ParseResult",
    "ValidationResult",
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

    def process_file(self, file_path: str) -> ValidationResult:
        """
        Parse and validate a single IDL file.

        Args:
            file_path: Path to .msg file

        Returns:
            ValidationResult with success status and any errors
        """

    def process_files(self, file_paths: List[str]) -> ValidationResult:
        """
        Parse and validate multiple IDL files.

        Args:
            file_paths: List of paths to .msg files

        Returns:
            ValidationResult with success status and any errors
        """

    def process_directory(self, directory: str, recursive: bool = True) -> ValidationResult:
        """
        Parse and validate all .msg files in a directory.

        Args:
            directory: Directory path
            recursive: Include subdirectories

        Returns:
            ValidationResult with success status and any errors
        """

    def generate_python(self, result: ValidationResult, output_dir: str):
        """Generate Python code from validated AST."""

    def generate_cpp(self, result: ValidationResult, output_dir: str):
        """Generate C++ code from validated AST."""

    def generate_json_schema(self, result: ValidationResult, output_file: str):
        """Generate JSON schema from validated AST."""


class ParseResult:
    """Result of parsing operation."""

    def __init__(self):
        self.files: Dict[Path, ParsedFile] = {}
        self.errors: List[ParseError] = []
        self.success: bool = True


class ValidationResult:
    """Result of validation operation."""

    def __init__(self):
        self.parsed_files: Dict[Path, ParsedFile] = {}
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.success: bool = True
        self.symbol_table: Optional[SymbolTable] = None

    def print_errors(self):
        """Print formatted errors and warnings."""

    def get_types(self) -> Dict[str, TypeInfo]:
        """Get all defined types."""
```

---

## Configuration (`lumos_idl/config.py`)

### Configuration File Format (`lumos.toml`)

```toml
[lumos]
# Version of the configuration format
version = "1.0"

[search_paths]
# Directories to search for imports
paths = [
    "interfaces",
    "common",
    "vendor"
]

[validation]
# Validation rules
enforce_field_numbering = false          # Require field numbers on all structs
allow_negative_field_numbers = false     # Allow negative field numbers
max_field_number = 536870911             # Max field number (protobuf limit)
warn_on_number_gaps = true               # Warn about gaps in field numbers
enforce_naming_conventions = false       # Enforce field/type naming rules

[naming]
# Naming conventions (if enforce_naming_conventions = true)
type_name_pattern = "^[A-Z][a-zA-Z0-9]*$"      # PascalCase
field_name_pattern = "^[a-z][a-z0-9_]*$"       # snake_case
constant_name_pattern = "^[A-Z][A-Z0-9_]*$"    # UPPER_SNAKE_CASE

[codegen]
# Code generation settings
python_output_dir = "generated/python"
cpp_output_dir = "generated/cpp"
generate_type_hints = true               # Python type hints
generate_validation = true               # Generate validation code
generate_serialization = true            # Generate serialization code

[codegen.python]
use_dataclasses = true
use_pydantic = false
target_version = "3.8"

[codegen.cpp]
standard = "c++17"
use_smart_pointers = true
namespace = "lumos"
```

### Configuration Class

```python
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import tomli  # TOML parser


@dataclass
class ValidationConfig:
    """Validation configuration."""
    enforce_field_numbering: bool = False
    allow_negative_field_numbers: bool = False
    max_field_number: int = 536870911
    warn_on_number_gaps: bool = True
    enforce_naming_conventions: bool = False


@dataclass
class NamingConfig:
    """Naming convention patterns."""
    type_name_pattern: str = "^[A-Z][a-zA-Z0-9]*$"
    field_name_pattern: str = "^[a-z][a-z0-9_]*$"
    constant_name_pattern: str = "^[A-Z][A-Z0-9_]*$"


@dataclass
class CodegenConfig:
    """Code generation configuration."""
    python_output_dir: Path = Path("generated/python")
    cpp_output_dir: Path = Path("generated/cpp")
    generate_type_hints: bool = True
    generate_validation: bool = True
    generate_serialization: bool = True


class Config:
    """Main configuration class."""

    def __init__(self):
        self.search_paths: List[Path] = [Path(".")]
        self.validation: ValidationConfig = ValidationConfig()
        self.naming: NamingConfig = NamingConfig()
        self.codegen: CodegenConfig = CodegenConfig()

    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        """Load configuration from TOML file."""
        with open(config_file, "rb") as f:
            data = tomli.load(f)

        config = cls()
        # Parse and populate from data
        return config

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls()

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""

    def save(self, config_file: str):
        """Save configuration to TOML file."""
```

---

## CLI Interface (`lumos_idl/__main__.py`)

```python
"""
Command-line interface for LumosInterface IDL.

Usage:
    # Validate files
    python -m lumos_idl validate interfaces/robot_state.msg

    # Validate directory
    python -m lumos_idl validate interfaces/ --recursive

    # Generate code
    python -m lumos_idl generate interfaces/ --lang python --output generated/

    # With config file
    python -m lumos_idl validate interfaces/ --config lumos.toml

    # Create default config
    python -m lumos_idl init
"""

import argparse
import sys
from pathlib import Path
from . import IDLProcessor, Config


def main():
    parser = argparse.ArgumentParser(
        prog="lumos_idl",
        description="LumosInterface IDL Parser and Validator"
    )

    parser.add_argument(
        "--config", "-c",
        help="Configuration file (lumos.toml)",
        default=None
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate IDL files")
    validate_parser.add_argument("files", nargs="+", help="Files or directories to validate")
    validate_parser.add_argument("--recursive", "-r", action="store_true", help="Recursive directory search")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate code")
    generate_parser.add_argument("files", nargs="+", help="Files or directories")
    generate_parser.add_argument("--lang", "-l", required=True, choices=["python", "cpp", "json"], help="Target language")
    generate_parser.add_argument("--output", "-o", required=True, help="Output directory")

    # Init command
    init_parser = subparsers.add_parser("init", help="Create default configuration")
    init_parser.add_argument("--output", "-o", default="lumos.toml", help="Output file")

    # Parse args
    args = parser.parse_args()

    # Load config
    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config.default()

    # Execute command
    if args.command == "validate":
        return cmd_validate(args, config)
    elif args.command == "generate":
        return cmd_generate(args, config)
    elif args.command == "init":
        return cmd_init(args)
    else:
        parser.print_help()
        return 1


def cmd_validate(args, config):
    """Execute validate command."""
    processor = IDLProcessor(config)

    # Collect files
    files = []
    for path_str in args.files:
        path = Path(path_str)
        if path.is_dir():
            if args.recursive:
                files.extend(path.rglob("*.msg"))
            else:
                files.extend(path.glob("*.msg"))
        else:
            files.append(path)

    # Validate
    result = processor.process_files([str(f) for f in files])

    # Print results
    if result.success:
        print(f"✓ Validation passed ({len(files)} files)")
        return 0
    else:
        result.print_errors()
        print(f"✗ Validation failed")
        return 1


def cmd_generate(args, config):
    """Execute generate command."""
    # Similar to validate, but also generate code
    pass


def cmd_init(args):
    """Create default configuration file."""
    config = Config.default()
    config.save(args.output)
    print(f"✓ Created configuration file: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## Usage Examples

### Python API

```python
# Example 1: Simple validation
from lumos_idl import IDLProcessor

processor = IDLProcessor()
result = processor.process_file("interfaces/robot_state.msg")

if result.success:
    print("✓ Valid")
else:
    result.print_errors()

# Example 2: With configuration
from lumos_idl import IDLProcessor, Config

config = Config.from_file("lumos.toml")
processor = IDLProcessor(config)
result = processor.process_directory("interfaces/", recursive=True)

if result.success:
    # Generate Python code
    processor.generate_python(result, output_dir="generated/python")

    # Access types
    for type_name, type_info in result.get_types().items():
        print(f"Type: {type_name}, Fields: {len(type_info.fields)}")

# Example 3: Custom configuration
from lumos_idl import IDLProcessor, Config

config = Config.default()
config.search_paths = [Path("interfaces"), Path("common")]
config.validation.enforce_field_numbering = True
config.validation.warn_on_number_gaps = True

processor = IDLProcessor(config)
result = processor.process_files([
    "interfaces/robot_state.msg",
    "interfaces/sensor_data.msg"
])
```

### Command Line

```bash
# Initialize project
python -m lumos_idl init

# Validate single file
python -m lumos_idl validate interfaces/robot_state.msg

# Validate directory
python -m lumos_idl validate interfaces/ --recursive

# Generate Python code
python -m lumos_idl generate interfaces/ \
    --lang python \
    --output generated/python

# With custom config
python -m lumos_idl validate interfaces/ \
    --config lumos.toml \
    --recursive
```

---

## Installation

### Development Installation

```bash
# Clone repository
git clone https://github.com/yourname/LumosInterface.git
cd LumosInterface

# Install in development mode
pip install -e .

# Or with poetry
poetry install
```

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lumos-idl"
version = "0.1.0"
description = "LumosInterface - A modern Interface Definition Language"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
dependencies = [
    "lark>=1.1.0",
    "tomli>=2.0.0; python_version < '3.11'",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "mypy>=0.990",
]

[project.scripts]
lumos-idl = "lumos_idl.__main__:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["lumos_idl*"]

[tool.setuptools.package-data]
lumos_idl = ["grammar/*.lark"]
```

---

## Migration Path

### Current State → New Structure

```
Current:
├── grammar/message.lark
├── indentation_preprocessor.py
├── main.py
├── test_*.py
└── tests/

New:
├── lumos_idl/                    # ← All logic moves here
│   ├── __init__.py               # ← Public API
│   ├── config.py                 # ← NEW
│   ├── parser/
│   │   ├── preprocessor.py       # ← indentation_preprocessor.py
│   │   └── ast_parser.py         # ← main.py logic
│   └── validator/                # ← NEW
├── grammar/                      # ← Stays
├── tests/                        # ← Reorganize
└── pyproject.toml                # ← NEW
```

### Migration Steps

1. **Create package structure**
   ```bash
   mkdir -p lumos_idl/{parser,validator,ast,codegen,utils}
   touch lumos_idl/__init__.py
   ```

2. **Move existing code**
   - `indentation_preprocessor.py` → `lumos_idl/parser/preprocessor.py`
   - `main.py` logic → `lumos_idl/parser/ast_parser.py`

3. **Create new modules**
   - `lumos_idl/config.py`
   - `lumos_idl/__main__.py`
   - `lumos_idl/validator/` (per VALIDATION_ARCHITECTURE.md)

4. **Create packaging**
   - `pyproject.toml`
   - Update imports

5. **Test migration**
   - Update tests to import from `lumos_idl`
   - Verify all tests pass

---

## Benefits of This Structure

✅ **Single Entry Point**: `IDLProcessor` class handles everything
✅ **Configuration**: Flexible config via TOML file
✅ **CLI Support**: Full command-line interface
✅ **Installable**: Proper Python package
✅ **Testable**: Clean separation of concerns
✅ **Extensible**: Easy to add new generators/validators
✅ **Professional**: Follows Python packaging standards

---

## Next Steps

1. Review this structure with stakeholders
2. Create the package skeleton
3. Migrate existing code
4. Implement validator (per VALIDATION_ARCHITECTURE.md)
5. Add code generators
6. Write comprehensive tests
7. Document and publish
