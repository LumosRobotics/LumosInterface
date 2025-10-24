"""
Command-line interface for LumosInterface IDL.

Usage:
    # Validate files
    python -m lumos_idl validate interfaces/robot_state.msg

    # Validate directory
    python -m lumos_idl validate interfaces/ --recursive

    # Generate code (not yet implemented)
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

    # Execute command
    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "generate":
        return cmd_generate(args)
    elif args.command == "init":
        return cmd_init(args)
    else:
        parser.print_help()
        return 1


def cmd_validate(args):
    """Execute validate command."""
    # Load config
    if args.config:
        try:
            config = Config.from_file(args.config)
        except Exception as e:
            print(f"Error loading config: {e}")
            return 1
    else:
        config = Config.default()

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

    if not files:
        print("No .msg files found")
        return 1

    print(f"Validating {len(files)} file(s)...")

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


def cmd_generate(args):
    """Execute generate command."""
    print("Code generation not yet implemented")
    return 1


def cmd_init(args):
    """Create default configuration file."""
    output_path = Path(args.output)

    if output_path.exists():
        response = input(f"{args.output} already exists. Overwrite? [y/N] ")
        if response.lower() != 'y':
            print("Aborted")
            return 0

    # Create default TOML content
    default_toml = """[lumos]
version = "1.0"

[search_paths]
paths = [
    "interfaces",
    "common",
]

[validation]
enforce_field_numbering = false
allow_negative_field_numbers = false
max_field_number = 536870911
warn_on_number_gaps = true
enforce_naming_conventions = false

[naming]
type_name_pattern = "^[A-Z][a-zA-Z0-9]*$"
field_name_pattern = "^[a-z][a-z0-9_]*$"
constant_name_pattern = "^[A-Z][A-Z0-9_]*$"

[codegen]
python_output_dir = "generated/python"
cpp_output_dir = "generated/cpp"
generate_type_hints = true
generate_validation = true
generate_serialization = true

[codegen.python]
use_dataclasses = true
use_pydantic = false
target_version = "3.8"

[codegen.cpp]
standard = "c++17"
use_smart_pointers = true
namespace = "lumos"
"""

    with open(output_path, "w") as f:
        f.write(default_toml)

    print(f"✓ Created configuration file: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
