"""
Configuration management for LumosInterface IDL.

Handles loading and managing configuration from TOML files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import sys

# Use tomli for Python < 3.11, tomllib for 3.11+
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class ValidationConfig:
    """Validation configuration."""
    enforce_field_numbering: bool = False
    allow_negative_field_numbers: bool = False
    max_field_number: int = 536870911  # Protobuf limit: 2^29 - 1
    warn_on_number_gaps: bool = True
    enforce_naming_conventions: bool = False


@dataclass
class NamingConfig:
    """Naming convention patterns."""
    type_name_pattern: str = "^[A-Z][a-zA-Z0-9]*$"  # PascalCase
    field_name_pattern: str = "^[a-z][a-z0-9_]*$"   # snake_case
    constant_name_pattern: str = "^[A-Z][A-Z0-9_]*$"  # UPPER_SNAKE_CASE


@dataclass
class PythonCodegenConfig:
    """Python-specific code generation settings."""
    use_dataclasses: bool = True
    use_pydantic: bool = False
    target_version: str = "3.8"


@dataclass
class CppCodegenConfig:
    """C++-specific code generation settings."""
    standard: str = "c++17"
    use_smart_pointers: bool = True
    namespace: str = "lumos"


@dataclass
class AttributeConfig:
    """Attribute system configuration."""
    enabled_schemas: List[str] = field(default_factory=list)
    custom_schemas: List[Path] = field(default_factory=list)
    warn_unknown_attributes: bool = True
    strict_mode: bool = False


@dataclass
class CodegenConfig:
    """Code generation configuration."""
    python_output_dir: Path = field(default_factory=lambda: Path("generated/python"))
    cpp_output_dir: Path = field(default_factory=lambda: Path("generated/cpp"))
    generate_type_hints: bool = True
    generate_validation: bool = True
    generate_serialization: bool = True
    python: PythonCodegenConfig = field(default_factory=PythonCodegenConfig)
    cpp: CppCodegenConfig = field(default_factory=CppCodegenConfig)


class Config:
    """Main configuration class."""

    def __init__(self):
        self.search_paths: List[Path] = [Path(".")]
        self.validation: ValidationConfig = ValidationConfig()
        self.naming: NamingConfig = NamingConfig()
        self.codegen: CodegenConfig = CodegenConfig()
        self.attributes: AttributeConfig = AttributeConfig()

    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        """Load configuration from TOML file."""
        if tomllib is None:
            raise ImportError(
                "tomli package is required for Python < 3.11. "
                "Install with: pip install tomli"
            )

        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        config = cls()

        # Parse search paths
        if "search_paths" in data and "paths" in data["search_paths"]:
            config.search_paths = [Path(p) for p in data["search_paths"]["paths"]]

        # Parse validation config
        if "validation" in data:
            val_data = data["validation"]
            config.validation = ValidationConfig(
                enforce_field_numbering=val_data.get("enforce_field_numbering", False),
                allow_negative_field_numbers=val_data.get("allow_negative_field_numbers", False),
                max_field_number=val_data.get("max_field_number", 536870911),
                warn_on_number_gaps=val_data.get("warn_on_number_gaps", True),
                enforce_naming_conventions=val_data.get("enforce_naming_conventions", False),
            )

        # Parse naming config
        if "naming" in data:
            nam_data = data["naming"]
            config.naming = NamingConfig(
                type_name_pattern=nam_data.get("type_name_pattern", "^[A-Z][a-zA-Z0-9]*$"),
                field_name_pattern=nam_data.get("field_name_pattern", "^[a-z][a-z0-9_]*$"),
                constant_name_pattern=nam_data.get("constant_name_pattern", "^[A-Z][A-Z0-9_]*$"),
            )

        # Parse attributes config
        if "attributes" in data:
            attr_data = data["attributes"]
            config.attributes = AttributeConfig(
                enabled_schemas=attr_data.get("enabled_schemas", []),
                custom_schemas=[Path(p) for p in attr_data.get("custom_schemas", [])],
                warn_unknown_attributes=attr_data.get("warn_unknown_attributes", True),
                strict_mode=attr_data.get("strict_mode", False),
            )

        # Parse codegen config
        if "codegen" in data:
            cg_data = data["codegen"]
            python_cfg = PythonCodegenConfig()
            cpp_cfg = CppCodegenConfig()

            if "python" in cg_data:
                py_data = cg_data["python"]
                python_cfg = PythonCodegenConfig(
                    use_dataclasses=py_data.get("use_dataclasses", True),
                    use_pydantic=py_data.get("use_pydantic", False),
                    target_version=py_data.get("target_version", "3.8"),
                )

            if "cpp" in cg_data:
                cpp_data = cg_data["cpp"]
                cpp_cfg = CppCodegenConfig(
                    standard=cpp_data.get("standard", "c++17"),
                    use_smart_pointers=cpp_data.get("use_smart_pointers", True),
                    namespace=cpp_data.get("namespace", "lumos"),
                )

            config.codegen = CodegenConfig(
                python_output_dir=Path(cg_data.get("python_output_dir", "generated/python")),
                cpp_output_dir=Path(cg_data.get("cpp_output_dir", "generated/cpp")),
                generate_type_hints=cg_data.get("generate_type_hints", True),
                generate_validation=cg_data.get("generate_validation", True),
                generate_serialization=cg_data.get("generate_serialization", True),
                python=python_cfg,
                cpp=cpp_cfg,
            )

        return config

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "search_paths": {
                "paths": [str(p) for p in self.search_paths]
            },
            "validation": {
                "enforce_field_numbering": self.validation.enforce_field_numbering,
                "allow_negative_field_numbers": self.validation.allow_negative_field_numbers,
                "max_field_number": self.validation.max_field_number,
                "warn_on_number_gaps": self.validation.warn_on_number_gaps,
                "enforce_naming_conventions": self.validation.enforce_naming_conventions,
            },
            "naming": {
                "type_name_pattern": self.naming.type_name_pattern,
                "field_name_pattern": self.naming.field_name_pattern,
                "constant_name_pattern": self.naming.constant_name_pattern,
            },
            "attributes": {
                "enabled_schemas": self.attributes.enabled_schemas,
                "custom_schemas": [str(p) for p in self.attributes.custom_schemas],
                "warn_unknown_attributes": self.attributes.warn_unknown_attributes,
                "strict_mode": self.attributes.strict_mode,
            },
            "codegen": {
                "python_output_dir": str(self.codegen.python_output_dir),
                "cpp_output_dir": str(self.codegen.cpp_output_dir),
                "generate_type_hints": self.codegen.generate_type_hints,
                "generate_validation": self.codegen.generate_validation,
                "generate_serialization": self.codegen.generate_serialization,
                "python": {
                    "use_dataclasses": self.codegen.python.use_dataclasses,
                    "use_pydantic": self.codegen.python.use_pydantic,
                    "target_version": self.codegen.python.target_version,
                },
                "cpp": {
                    "standard": self.codegen.cpp.standard,
                    "use_smart_pointers": self.codegen.cpp.use_smart_pointers,
                    "namespace": self.codegen.cpp.namespace,
                },
            },
        }

    def save(self, config_file: str):
        """Save configuration to TOML file."""
        try:
            import tomli_w
        except ImportError:
            raise ImportError(
                "tomli_w package is required for saving TOML files. "
                "Install with: pip install tomli-w"
            )

        config_path = Path(config_file)
        with open(config_path, "wb") as f:
            tomli_w.dump(self.to_dict(), f)
