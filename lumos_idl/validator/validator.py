"""
Main validator orchestrator for LumosInterface IDL.

Coordinates all validation phases.
"""

from pathlib import Path
from typing import List, Set, Optional, Any, Dict, Tuple
from lark import Tree

from .symbol_table import SymbolTable
from .error_reporter import ErrorReporter
from .field_validator import FieldValidator
from .enum_validator import EnumValidator
from .collection_validator import CollectionValidator
from .import_resolver import ImportResolver
from ..attributes import AttributeRegistry, AttributeValidator
from ..ast.types import (
    ValidationResult,
    ValidationError,
    FileInfo,
    TypeInfo,
    FieldInfo,
    EnumMemberInfo,
    AliasInfo,
)
from ..config import Config


class IDLValidator:
    """Main validator orchestrator."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize validator.

        Args:
            config: Configuration object
        """
        self.config = config or Config.default()
        self.symbol_table = SymbolTable()
        self.error_reporter = ErrorReporter()
        self.field_validator = FieldValidator(config)
        self.enum_validator = EnumValidator(config)
        self.collection_validator = CollectionValidator(config)
        self.import_resolver = ImportResolver(config.search_paths)

        # Attribute validation system
        self.attribute_registry = AttributeRegistry()
        self.attribute_registry.load_builtin_schemas()

        # Load custom schemas if configured
        for schema_path in self.config.attributes.custom_schemas:
            try:
                self.attribute_registry.load_schema(schema_path)
            except Exception as e:
                # Log error but don't fail initialization
                pass

        # Create attribute validator if schemas are enabled
        self.attribute_validator = None
        if self.config.attributes.enabled_schemas:
            self.attribute_validator = AttributeValidator(
                self.attribute_registry,
                self.config.attributes.enabled_schemas,
                self.config.attributes.warn_unknown_attributes
            )

        # Primitive types
        self.primitive_types = {
            "bool",
            "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64",
            "float32", "float64",
            "string", "bytes",
        }

    def validate(self, parse_result: ValidationResult) -> ValidationResult:
        """
        Validate parsed files.

        Args:
            parse_result: ValidationResult from parsing phase

        Returns:
            Updated ValidationResult with validation errors
        """
        # Clear previous state
        self.symbol_table.clear()
        self.error_reporter.clear()

        # If parsing failed, return early
        if not parse_result.success:
            return parse_result

        # Phase 1: Register all files and extract type definitions
        for file_path, file_info in parse_result.parsed_files.items():
            self._register_file(file_info)

        # Phase 2: Build symbol table
        for file_path, file_info in parse_result.parsed_files.items():
            self._extract_types(file_info)

        # Phase 2.5: Validate collections (needs AST access)
        for file_path, file_info in parse_result.parsed_files.items():
            self._validate_collections(file_info)

        # Phase 3: Validate type references (basic for now)
        for file_path, file_info in parse_result.parsed_files.items():
            self._validate_file_types(file_info)

        # Phase 4: Validate field rules
        for type_info in self.symbol_table.types.values():
            if type_info.kind in ("struct", "interface"):
                field_errors = self.field_validator.validate_type(type_info)
                for error in field_errors:
                    self.error_reporter.add_error(error)
            elif type_info.kind == "enum":
                enum_errors = self.enum_validator.validate_enum(type_info)
                for error in enum_errors:
                    self.error_reporter.add_error(error)

        # Phase 5: Validate imports and cross-file dependencies
        import_errors = self.import_resolver.validate_imports(parse_result.parsed_files)
        for error in import_errors:
            self.error_reporter.add_error(error)

        # Phase 6: Validate attributes (if enabled)
        if self.attribute_validator is not None:
            for type_info in self.symbol_table.types.values():
                # Validate struct/enum attributes
                if type_info.kind == "struct":
                    struct_attr_errors = self.attribute_validator.validate_struct_attributes(type_info)
                    for error in struct_attr_errors:
                        self.error_reporter.add_error(error)
                elif type_info.kind == "enum":
                    enum_attr_errors = self.attribute_validator.validate_enum_attributes(type_info)
                    for error in enum_attr_errors:
                        self.error_reporter.add_error(error)

                # Validate field attributes
                for field in type_info.fields:
                    # Temporarily set file_path on field for validation
                    field.file_path = type_info.file_path
                    field_attr_errors = self.attribute_validator.validate_field_attributes(field)
                    for error in field_attr_errors:
                        self.error_reporter.add_error(error)

        # Add collected errors to result
        for error in self.error_reporter.errors:
            parse_result.add_error(error)
        for warning in self.error_reporter.warnings:
            parse_result.add_error(warning)

        # Update success status
        if self.error_reporter.has_errors():
            parse_result.success = False

        return parse_result

    def _register_file(self, file_info: FileInfo):
        """
        Register a file in the symbol table.

        Args:
            file_info: FileInfo to register
        """
        self.symbol_table.register_file(file_info)

    def _extract_types(self, file_info: FileInfo):
        """
        Extract type definitions from a file's AST.

        Args:
            file_info: FileInfo with AST to process
        """
        if file_info.ast is None:
            return

        # Extract struct definitions
        for struct_node in file_info.ast.find_data("struct_def"):
            self._extract_struct(struct_node, file_info)

        # Extract interface definitions
        for interface_node in file_info.ast.find_data("interface_def"):
            self._extract_interface(interface_node, file_info)

        # Extract enum definitions
        for enum_node in file_info.ast.find_data("enum_def"):
            self._extract_enum(enum_node, file_info)

        # Extract type aliases
        for alias_node in file_info.ast.find_data("using_def"):
            self._extract_alias(alias_node, file_info)

    def _extract_struct(self, struct_node: Tree, file_info: FileInfo):
        """
        Extract a struct definition.

        Args:
            struct_node: AST node for struct
            file_info: FileInfo containing the struct
        """
        # Get struct name (children[1], children[0] is STRUCT token)
        struct_name = struct_node.children[1].value

        # Create qualified name
        qualified_name = f"{file_info.namespace}::{struct_name}"

        # Extract fields
        fields = self._extract_fields(struct_node)

        # Extract struct-level attributes
        struct_attributes = self._extract_struct_attributes(struct_node)

        # Create TypeInfo
        type_info = TypeInfo(
            name=struct_name,
            qualified_name=qualified_name,
            kind="struct",
            file_path=file_info.path,
            ast_node=struct_node,
            fields=fields,
            struct_attributes=struct_attributes,
        )

        # Register in symbol table
        self.symbol_table.register_type(type_info)

        # Add to file's defined types
        file_info.defined_types.append(type_info)

    def _extract_interface(self, interface_node: Tree, file_info: FileInfo):
        """
        Extract an interface definition.

        Args:
            interface_node: AST node for interface
            file_info: FileInfo containing the interface
        """
        # Get interface name (children[1], children[0] is INTERFACE token)
        interface_name = interface_node.children[1].value

        # Create qualified name
        qualified_name = f"{file_info.namespace}::{interface_name}"

        # Extract fields
        fields = self._extract_fields(interface_node)

        # Extract struct-level attributes
        struct_attributes = self._extract_struct_attributes(interface_node)

        # Create TypeInfo
        type_info = TypeInfo(
            name=interface_name,
            qualified_name=qualified_name,
            kind="interface",
            file_path=file_info.path,
            ast_node=interface_node,
            fields=fields,
            struct_attributes=struct_attributes,
        )

        # Register in symbol table
        self.symbol_table.register_type(type_info)

        # Add to file's defined types
        file_info.defined_types.append(type_info)

    def _extract_enum(self, enum_node: Tree, file_info: FileInfo):
        """
        Extract an enum definition.

        Args:
            enum_node: AST node for enum
            file_info: FileInfo containing the enum
        """
        # enum_def children: ENUM, CNAME, [primitive_type], NEWLINE, INDENT, enum_body, DEDENT
        # Get enum name (children[1])
        enum_name = enum_node.children[1].value

        # Create qualified name
        qualified_name = f"{file_info.namespace}::{enum_name}"

        # Extract storage type (if specified)
        storage_type = "int32"  # Default
        has_storage_type = False

        # Check if there's a storage type specified (children[2] might be primitive_type)
        for child in enum_node.children:
            if hasattr(child, 'data') and child.data == 'primitive_type':
                # Extract the actual type token
                if len(child.children) > 0:
                    storage_type = child.children[0].value
                has_storage_type = True
                break

        # Extract enum members with auto-increment
        members = self._extract_enum_members(enum_node)

        # Extract enum-level attributes (enums use struct_attributes field)
        enum_attributes = {}  # TODO: Extract enum attributes if grammar supports them

        # Create TypeInfo
        type_info = TypeInfo(
            name=enum_name,
            qualified_name=qualified_name,
            kind="enum",
            file_path=file_info.path,
            ast_node=enum_node,
            enum_members=members,
            enum_storage_type=storage_type,
            struct_attributes=enum_attributes,
        )

        # Register in symbol table
        self.symbol_table.register_type(type_info)

        # Add to file's defined types
        file_info.defined_types.append(type_info)

    def _extract_enum_members(self, enum_node: Tree) -> List[EnumMemberInfo]:
        """
        Extract enum members with auto-increment.

        Args:
            enum_node: AST node for enum

        Returns:
            List of EnumMemberInfo with resolved values
        """
        members = []
        next_value = 0  # Default starting value

        # Find enum_body
        for body_node in enum_node.find_data("enum_body"):
            for member_node in body_node.find_data("enum_member"):
                # enum_member children: CNAME, [EQUAL, SIGNED_INT], NEWLINE
                member_name = member_node.children[0].value

                # Check if explicit value is provided
                explicit_value = None
                for i, child in enumerate(member_node.children):
                    if hasattr(child, 'type') and child.type == 'SIGNED_INT':
                        explicit_value = int(child.value)
                        break

                if explicit_value is not None:
                    # Use explicit value
                    member_value = explicit_value
                    next_value = member_value + 1
                else:
                    # Use auto-increment
                    member_value = next_value
                    next_value += 1

                # Get line number
                line_number = 0
                if hasattr(member_node.meta, 'line'):
                    line_number = member_node.meta.line

                members.append(EnumMemberInfo(
                    name=member_name,
                    value=member_value,
                    line_number=line_number,
                ))

        return members

    def _extract_alias(self, alias_node: Tree, file_info: FileInfo):
        """
        Extract a type alias definition.

        Args:
            alias_node: AST node for using_def
            file_info: FileInfo containing the alias
        """
        # using_def children: CNAME (alias name), primitive_type
        # Get alias name (children[0])
        alias_name = alias_node.children[0].value

        # Get target type (children[1] is primitive_type)
        target_type = None
        if len(alias_node.children) > 1:
            prim_type_node = alias_node.children[1]
            if hasattr(prim_type_node, 'data') and prim_type_node.data == 'primitive_type':
                # The primitive_type node has the actual type as a token
                if len(prim_type_node.children) > 0:
                    target_type = prim_type_node.children[0].value
                else:
                    # Sometimes it's directly the type token
                    target_type = prim_type_node.value

        if target_type is None:
            return  # Skip invalid alias

        # Create qualified name
        qualified_name = f"{file_info.namespace}::{alias_name}"

        # Get line number
        line_number = 0
        if hasattr(alias_node.meta, 'line'):
            line_number = alias_node.meta.line

        # Create AliasInfo
        alias_info = AliasInfo(
            name=alias_name,
            target_type=target_type,
            qualified_name=qualified_name,
            file_path=file_info.path,
            line_number=line_number,
        )

        # Register in symbol table
        self.symbol_table.register_alias(alias_info)

        # Add to file's defined aliases
        file_info.defined_aliases.append(alias_info)

    def _extract_fields(self, type_node: Tree) -> List[FieldInfo]:
        """
        Extract fields from a struct or interface.

        Args:
            type_node: AST node for struct or interface

        Returns:
            List of FieldInfo
        """
        fields = []

        # Find struct_body
        for body_node in type_node.find_data("struct_body"):
            # Fields can be direct children (for simple cases) or in struct_field nodes
            for child in body_node.children:
                if hasattr(child, 'data'):
                    field_info = None
                    if child.data == 'struct_field':
                        field_info = self._extract_field(child)
                    elif child.data in ('primitive_type_field', 'user_type_field', 'qualified_type_field', 'collection_type_field'):
                        # Direct field node
                        field_info = self._extract_direct_field(child)

                    if field_info:
                        fields.append(field_info)

        return fields

    def _extract_field(self, field_node: Tree) -> Optional[FieldInfo]:
        """
        Extract a single field.

        Args:
            field_node: AST node for field (struct_field node)

        Returns:
            FieldInfo or None if extraction fails
        """
        try:
            # Determine if field is optional
            optional = False
            start_idx = 0

            if len(field_node.children) > 0 and hasattr(field_node.children[0], 'type'):
                if field_node.children[0].type == 'OPTIONAL':
                    optional = True
                    start_idx = 1

            # struct_field children: type_node, field_name_token, [field_number], [inline_attrs], [NEWLINE], [field_attrs]
            # The type is directly in children (primitive_type tree or CNAME token or qualified_type tree)
            if len(field_node.children) < start_idx + 2:
                return None

            type_node = field_node.children[start_idx]
            name_token = field_node.children[start_idx + 1]

            # Extract type name
            type_name = None
            if hasattr(type_node, 'value'):
                # Direct token (CNAME for user types)
                type_name = type_node.value
            elif hasattr(type_node, 'data'):
                if type_node.data == 'primitive_type':
                    # primitive_type tree with actual type token
                    if len(type_node.children) > 0:
                        type_name = type_node.children[0].value
                elif type_node.data == 'qualified_type':
                    # Qualified type like common::geometry::Vector3
                    parts = []
                    for child in type_node.children:
                        if hasattr(child, 'value'):
                            parts.append(child.value)
                    type_name = "::".join(parts)
                elif type_node.data == 'collection_type':
                    # Collection type - simplified
                    type_name = "array"

            # Extract field name
            field_name = None
            if hasattr(name_token, 'value'):
                field_name = name_token.value

            if type_name is None or field_name is None:
                return None

            # Extract field number if present
            field_number = None
            for child in field_node.children:
                if hasattr(child, 'data') and child.data == 'field_number':
                    # Field number is the integer value
                    field_number = int(child.children[0].value)

            # Get line number
            line_number = 0
            if hasattr(field_node.meta, 'line'):
                line_number = field_node.meta.line

            # Extract attributes
            inline_attrs, indented_attrs = self._extract_field_attributes(field_node)

            return FieldInfo(
                name=field_name,
                type_name=type_name,
                field_number=field_number,
                optional=optional,
                inline_attributes=inline_attrs,
                indented_attributes=indented_attrs,
                line_number=line_number,
            )

        except Exception as e:
            # Log error but don't fail
            return None

    def _extract_direct_field(self, field_node: Tree) -> Optional[FieldInfo]:
        """
        Extract a direct field node (not wrapped in struct_field).

        Args:
            field_node: AST node for primitive_type_field, user_type_field, etc.

        Returns:
            FieldInfo or None if extraction fails
        """
        try:
            type_name = None
            field_name = None
            optional = False

            # Check if first child is OPTIONAL token
            start_idx = 0
            if len(field_node.children) > 0 and hasattr(field_node.children[0], 'type'):
                if field_node.children[0].type == 'OPTIONAL':
                    optional = True
                    start_idx = 1

            if field_node.data == 'primitive_type_field':
                # primitive_type_field: [OPTIONAL] primitive_type CNAME ...
                if len(field_node.children) >= start_idx + 2:
                    prim_type = field_node.children[start_idx]
                    if hasattr(prim_type, 'children') and len(prim_type.children) > 0:
                        type_name = prim_type.children[0].value
                    field_name = field_node.children[start_idx + 1].value

            elif field_node.data == 'user_type_field':
                # user_type_field: [OPTIONAL] CNAME CNAME ...
                if len(field_node.children) >= start_idx + 2:
                    type_name = field_node.children[start_idx].value
                    field_name = field_node.children[start_idx + 1].value

            elif field_node.data == 'qualified_type_field':
                # qualified_type_field: qualified_type CNAME ...
                if len(field_node.children) >= 2:
                    qualified_type = field_node.children[0]
                    parts = []
                    for child in qualified_type.children:
                        if hasattr(child, 'value'):
                            parts.append(child.value)
                    type_name = "::".join(parts)
                    field_name = field_node.children[1].value

            elif field_node.data == 'collection_type_field':
                # collection_type_field: collection_type CNAME ...
                if len(field_node.children) >= 2:
                    type_name = "array"  # Simplified
                    field_name = field_node.children[1].value

            if type_name is None or field_name is None:
                return None

            # Extract field number if present
            field_number = None
            for child in field_node.children:
                if hasattr(child, 'data') and child.data == 'field_number':
                    # Field number is the integer value
                    if len(child.children) > 0:
                        field_number = int(child.children[0].value)
                    break

            # Get line number
            line_number = 0
            if hasattr(field_node.meta, 'line'):
                line_number = field_node.meta.line

            # Extract attributes
            inline_attrs, indented_attrs = self._extract_field_attributes(field_node)

            return FieldInfo(
                name=field_name,
                type_name=type_name,
                field_number=field_number,
                optional=optional,
                inline_attributes=inline_attrs,
                indented_attributes=indented_attrs,
                line_number=line_number,
            )

        except Exception as e:
            return None

    def _validate_collections(self, file_info: FileInfo):
        """
        Validate collection types in a file.

        Args:
            file_info: FileInfo to validate
        """
        if file_info.ast is None:
            return

        # Find all struct and interface definitions
        for struct_node in file_info.ast.find_data("struct_def"):
            self._validate_collection_fields(struct_node, file_info)

        for interface_node in file_info.ast.find_data("interface_def"):
            self._validate_collection_fields(interface_node, file_info)

    def _validate_collection_fields(self, type_node: Tree, file_info: FileInfo):
        """Validate collection fields in a struct or interface."""
        # Find all fields with collection types
        for body_node in type_node.find_data("struct_body"):
            for field_node in body_node.children:
                if hasattr(field_node, 'data') and field_node.data == 'collection_type_field':
                    # Get line number
                    line_number = 0
                    if hasattr(field_node.meta, 'line'):
                        line_number = field_node.meta.line

                    # Validate the collection
                    errors = self.collection_validator.validate_collection_field(
                        field_node, file_info.path, line_number)

                    for error in errors:
                        self.error_reporter.add_error(error)

    def _validate_file_types(self, file_info: FileInfo):
        """
        Validate type references in a file.

        Args:
            file_info: FileInfo to validate
        """
        # For each type defined in the file
        for type_info in file_info.defined_types:
            # Validate each field's type
            for field in type_info.fields:
                self._validate_field_type(field, type_info, file_info)

    def _validate_field_type(self, field: FieldInfo, type_info: TypeInfo, file_info: FileInfo):
        """
        Validate a field's type reference.

        Args:
            field: FieldInfo to validate
            type_info: TypeInfo containing the field
            file_info: FileInfo context
        """
        type_name = field.type_name

        # Check if primitive type
        if type_name in self.primitive_types:
            return  # Valid

        # Check if it's a collection type (basic check)
        if type_name in ('array', 'matrix', 'tensor'):
            return  # Valid (full collection validation in later phase)

        # Try to resolve as a type alias first
        resolved_alias = self.symbol_table.lookup_alias(type_name, file_info)
        if resolved_alias is not None:
            # Alias found - validate the target type
            target_type = resolved_alias.target_type
            if target_type in self.primitive_types:
                return  # Valid alias to primitive
            # Could also check if target is another alias (recursive), but keep it simple for now
            return  # Valid alias

        # Try to resolve the type
        resolved_type = self.symbol_table.lookup_type(type_name, file_info)

        if resolved_type is None:
            # Type not found
            self.error_reporter.add_error(ValidationError(
                file_path=type_info.file_path,
                line=field.line_number,
                column=0,
                message=f"Type '{type_name}' not found for field '{field.name}'",
                error_type="type_not_found",
                severity="error"
            ))

    def get_symbol_table(self) -> SymbolTable:
        """Get the symbol table."""
        return self.symbol_table

    def get_error_reporter(self) -> ErrorReporter:
        """Get the error reporter."""
        return self.error_reporter

    def _extract_struct_attributes(self, type_node: Tree) -> Dict[str, Any]:
        """
        Extract struct-level attributes from AST.

        Args:
            type_node: Struct, interface, or enum AST node

        Returns:
            Dictionary of attributes
        """
        attributes: Dict[str, Any] = {}

        # Find struct_body
        for body_node in type_node.find_data("struct_body"):
            # Check for struct_attributes node
            for child in body_node.children:
                if hasattr(child, 'data') and child.data == 'struct_attributes':
                    # Extract all attribute entries
                    for attr_entry in child.find_data("simple_attribute"):
                        # simple_attribute: CNAME ":" simple_value NEWLINE
                        if len(attr_entry.children) >= 2:
                            attr_name = attr_entry.children[0].value
                            attr_value = self._extract_attribute_value(attr_entry.children[1])
                            attributes[attr_name] = attr_value

                    for attr_entry in child.find_data("object_attribute"):
                        # object_attribute: CNAME ":" NEWLINE INDENT attribute_entry+ DEDENT
                        if len(attr_entry.children) >= 1:
                            attr_name = attr_entry.children[0].value
                            # Extract nested attributes
                            nested_attrs = {}
                            for nested_entry in attr_entry.find_data("simple_attribute"):
                                if len(nested_entry.children) >= 2:
                                    nested_name = nested_entry.children[0].value
                                    nested_value = self._extract_attribute_value(nested_entry.children[1])
                                    nested_attrs[nested_name] = nested_value
                            attributes[attr_name] = nested_attrs

        # Also check enum_def for enum attributes
        if hasattr(type_node, 'data') and type_node.data == 'enum_def':
            # Enums might have attributes too - similar extraction
            pass

        return attributes

    def _extract_attribute_value(self, value_node: Tree) -> Any:
        """
        Extract an attribute value from AST.

        Args:
            value_node: simple_value AST node

        Returns:
            Python value (int, float, str, bool)
        """
        if not hasattr(value_node, 'data'):
            return None

        if value_node.data == 'bool_true':
            return True
        elif value_node.data == 'bool_false':
            return False
        elif value_node.data == 'int_value':
            if len(value_node.children) > 0:
                return int(value_node.children[0].value)
        elif value_node.data == 'float_value':
            if len(value_node.children) > 0:
                return float(value_node.children[0].value)
        elif value_node.data in ('string_value', 'multiline_string_value'):
            if len(value_node.children) > 0:
                # Remove quotes from string
                string_val = value_node.children[0].value
                if string_val.startswith('"""') and string_val.endswith('"""'):
                    return string_val[3:-3]
                elif string_val.startswith('"') and string_val.endswith('"'):
                    return string_val[1:-1]
                elif string_val.startswith("'") and string_val.endswith("'"):
                    return string_val[1:-1]
                return string_val

        return None

    def _extract_field_attributes(self, field_node: Tree) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract field attributes (both inline and indented).

        Args:
            field_node: AST node for field

        Returns:
            Tuple of (inline_attributes, indented_attributes)
        """
        inline_attrs: Dict[str, Any] = {}
        indented_attrs: Dict[str, Any] = {}

        # Extract indented attributes
        for attr_block in field_node.find_data("field_attributes"):
            for attr_entry in attr_block.find_data("simple_attribute"):
                if len(attr_entry.children) >= 2:
                    attr_name = attr_entry.children[0].value
                    attr_value = self._extract_attribute_value(attr_entry.children[1])
                    indented_attrs[attr_name] = attr_value

            for attr_entry in attr_block.find_data("object_attribute"):
                if len(attr_entry.children) >= 1:
                    attr_name = attr_entry.children[0].value
                    nested_attrs = {}
                    for nested_entry in attr_entry.find_data("simple_attribute"):
                        if len(nested_entry.children) >= 2:
                            nested_name = nested_entry.children[0].value
                            nested_value = self._extract_attribute_value(nested_entry.children[1])
                            nested_attrs[nested_name] = nested_value
                    indented_attrs[attr_name] = nested_attrs

        # TODO: Extract inline attributes if needed

        return (inline_attrs, indented_attrs)
