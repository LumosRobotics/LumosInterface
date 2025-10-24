# C++ Code Generator Architecture (Simplified)

## Overview

Generate C++ code from validated LumosInterface IDL using direct string building. No external template engines required - just Python string formatting and simple code builders.

---

## Design Philosophy

**Keep It Simple:**
- Direct string building with f-strings and multi-line strings
- No external dependencies beyond Python stdlib
- Clear, readable generation code
- Easy to understand and modify

**When Jinja2 Makes Sense:**
- Very complex template logic
- Many customization points
- Template inheritance needed
- Non-programmer users editing templates

**For This Project:**
- Direct code building is clearer
- Less abstraction = easier debugging
- Templates can be added later if needed

---

## Architecture Components

```
generator/
├── cpp/
│   ├── __init__.py
│   ├── generator.py          # Main orchestrator
│   ├── type_mapper.py        # Type conversions
│   ├── code_builder.py       # Helper for building code
│   ├── struct_writer.py      # Struct generation
│   ├── enum_writer.py        # Enum generation
│   └── serialization_writer.py  # Serialization code
```

---

## Core Module: `code_builder.py`

**Purpose**: Helper class for building formatted C++ code

```python
class CodeBuilder:
    """Helper for building indented C++ code."""

    def __init__(self, indent_size: int = 2):
        self.lines: List[str] = []
        self.indent_level: int = 0
        self.indent_size: int = indent_size

    def add_line(self, line: str = ""):
        """Add a line with current indentation."""
        if line:
            indent = " " * (self.indent_level * self.indent_size)
            self.lines.append(f"{indent}{line}")
        else:
            self.lines.append("")

    def add_lines(self, lines: str):
        """Add multiple lines (handles multi-line strings)."""
        for line in lines.split('\n'):
            self.add_line(line)

    def indent(self):
        """Increase indentation level."""
        self.indent_level += 1

    def dedent(self):
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)

    def add_block(self, header: str, body_fn):
        """Add a block with automatic indentation."""
        self.add_line(f"{header} {{")
        self.indent()
        body_fn()
        self.dedent()
        self.add_line("}")

    def build(self) -> str:
        """Return the generated code as string."""
        return '\n'.join(self.lines)

    # Context manager support
    def __enter__(self):
        self.indent()
        return self

    def __exit__(self, *args):
        self.dedent()


# Usage example:
builder = CodeBuilder()
builder.add_line("struct Vector3 {")
with builder:
    builder.add_line("float x;")
    builder.add_line("float y;")
    builder.add_line("float z;")
builder.add_line("};")
```

---

## Module: `type_mapper.py`

**Purpose**: Convert IDL types to C++ types

```python
class TypeMapper:
    """Maps IDL types to C++ types."""

    PRIMITIVE_TYPES = {
        "bool": "bool",
        "int8": "int8_t",
        "int16": "int16_t",
        "int32": "int32_t",
        "int64": "int64_t",
        "uint8": "uint8_t",
        "uint16": "uint16_t",
        "uint32": "uint32_t",
        "uint64": "uint64_t",
        "float32": "float",
        "float64": "double",
        "string": "std::string",
        "bytes": "std::vector<uint8_t>",
    }

    def __init__(self, config: GeneratorConfig):
        self.config = config

    def to_cpp_type(self, field: FieldInfo, context: FileInfo) -> CppTypeInfo:
        """
        Convert IDL field type to C++ type.

        Returns CppTypeInfo with:
        - type_str: The C++ type as string
        - includes: Set of required includes
        """
        type_name = field.type_name

        # Primitive type
        if type_name in self.PRIMITIVE_TYPES:
            cpp_type = self.PRIMITIVE_TYPES[type_name]
            includes = self._get_primitive_includes(type_name)

            # Handle optional
            if field.optional:
                cpp_type = f"std::optional<{cpp_type}>"
                includes.add("<optional>")

            return CppTypeInfo(type_str=cpp_type, includes=includes)

        # Type alias
        alias = self.lookup_alias(type_name, context)
        if alias:
            return self.to_cpp_type_for_alias(alias, field.optional)

        # User-defined type
        # Resolve to namespace-qualified name
        qualified_name = self.resolve_qualified_name(type_name, context)
        includes = self._get_includes_for_type(qualified_name, context)

        cpp_type = self._to_cpp_namespace(qualified_name)

        if field.optional:
            cpp_type = f"std::optional<{cpp_type}>"
            includes.add("<optional>")

        return CppTypeInfo(type_str=cpp_type, includes=includes)

    def to_cpp_collection(self, collection_node: Tree, optional: bool) -> CppTypeInfo:
        """
        Convert collection type to C++.

        Examples:
        - array<float32, 3> → std::array<float, 3>
        - array<float32, ?> → std::vector<float>
        - matrix<float32, 3, 3> → std::array<std::array<float, 3>, 3>
        """
        # Parse collection info from AST node
        coll_type = self._extract_collection_type(collection_node)
        element_type = self._extract_element_type(collection_node)
        sizes = self._extract_sizes(collection_node)

        element_cpp = self.to_cpp_type_from_name(element_type)
        includes = element_cpp.includes.copy()

        if coll_type == "array":
            if sizes and sizes[0] != "?":
                # Fixed size
                cpp_type = f"std::array<{element_cpp.type_str}, {sizes[0]}>"
                includes.add("<array>")
            else:
                # Dynamic size
                cpp_type = f"std::vector<{element_cpp.type_str}>"
                includes.add("<vector>")

        elif coll_type == "matrix":
            # Nested arrays: matrix<T, R, C> → array<array<T, C>, R>
            cpp_type = f"std::array<std::array<{element_cpp.type_str}, {sizes[1]}>, {sizes[0]}>"
            includes.add("<array>")

        elif coll_type == "tensor":
            # Build nested arrays from innermost to outermost
            cpp_type = element_cpp.type_str
            for size in reversed(sizes):
                cpp_type = f"std::array<{cpp_type}, {size}>"
            includes.add("<array>")

        if optional:
            cpp_type = f"std::optional<{cpp_type}>"
            includes.add("<optional>")

        return CppTypeInfo(type_str=cpp_type, includes=includes)

    def _to_cpp_namespace(self, qualified_name: str) -> str:
        """
        Convert IDL qualified name to C++ namespace.

        Example: common::geometry::Vector3 → lumos::common::geometry::Vector3
        """
        parts = qualified_name.split("::")
        if self.config.namespace_prefix:
            parts.insert(0, self.config.namespace_prefix)
        return "::".join(parts)

    def _get_primitive_includes(self, type_name: str) -> Set[str]:
        """Get required includes for primitive type."""
        if type_name in ("int8", "int16", "int32", "int64",
                         "uint8", "uint16", "uint32", "uint64"):
            return {"<cstdint>"}
        elif type_name == "string":
            return {"<string>"}
        elif type_name == "bytes":
            return {"<vector>", "<cstdint>"}
        else:
            return set()

@dataclass
class CppTypeInfo:
    """Information about a C++ type."""
    type_str: str           # The C++ type string
    includes: Set[str]      # Required includes
```

---

## Module: `struct_writer.py`

**Purpose**: Generate struct definitions

```python
class StructWriter:
    """Generates C++ struct code."""

    def __init__(self, type_mapper: TypeMapper, config: GeneratorConfig):
        self.type_mapper = type_mapper
        self.config = config

    def write_struct(
        self,
        type_info: TypeInfo,
        builder: CodeBuilder,
        context: FileInfo
    ):
        """Write struct definition to code builder."""

        # Doc comment
        if self.config.generate_docs:
            builder.add_line(f"/// {type_info.name}")
            builder.add_line("///")
            builder.add_line(f"/// Generated from {context.path}")

        # Struct declaration
        builder.add_line(f"struct {type_info.name} {{")

        with builder:
            # Fields
            for field in type_info.fields:
                cpp_type = self.type_mapper.to_cpp_type(field, context)
                builder.add_line(f"{cpp_type.type_str} {field.name};")

            builder.add_line()

            # Constructors
            self._write_constructors(type_info, builder, context)

            # Operators
            if self.config.generate_equality:
                builder.add_line()
                self._write_equality_operators(type_info, builder)

            # Serialization
            if self.config.generate_serialization:
                builder.add_line()
                self._write_serialization_methods(type_info, builder)

        builder.add_line("};")

    def _write_constructors(
        self,
        type_info: TypeInfo,
        builder: CodeBuilder,
        context: FileInfo
    ):
        """Write constructor declarations."""
        # Default constructor
        builder.add_line(f"/// Default constructor")
        builder.add_line(f"{type_info.name}() = default;")

        # Don't generate value constructor if too many fields
        if len(type_info.fields) > 0 and len(type_info.fields) <= 10:
            builder.add_line()
            builder.add_line(f"/// Value constructor")
            self._write_value_constructor(type_info, builder, context)

    def _write_value_constructor(
        self,
        type_info: TypeInfo,
        builder: CodeBuilder,
        context: FileInfo
    ):
        """Write value constructor."""
        # Constructor signature
        params = []
        for field in type_info.fields:
            cpp_type = self.type_mapper.to_cpp_type(field, context)
            params.append(f"{cpp_type.type_str} {field.name}_")

        builder.add_line(f"{type_info.name}(")
        with builder:
            for i, param in enumerate(params):
                comma = "," if i < len(params) - 1 else ""
                builder.add_line(f"{param}{comma}")
        builder.add_line(")")

        # Initializer list
        init_list = [f"{f.name}({f.name}_)" for f in type_info.fields]
        if init_list:
            builder.add_line(f"  : {', '.join(init_list)} {{}}")
        else:
            builder.add_line("  {}")

    def _write_equality_operators(
        self,
        type_info: TypeInfo,
        builder: CodeBuilder
    ):
        """Write operator== and operator!=."""
        builder.add_line(f"/// Equality comparison")
        builder.add_line(f"bool operator==(const {type_info.name}& other) const {{")
        with builder:
            if not type_info.fields:
                builder.add_line("return true;")
            else:
                # Build comparison expression
                comparisons = [f"{f.name} == other.{f.name}" for f in type_info.fields]
                if len(comparisons) == 1:
                    builder.add_line(f"return {comparisons[0]};")
                else:
                    builder.add_line("return " + comparisons[0])
                    with builder:
                        for comp in comparisons[1:-1]:
                            builder.add_line(f"&& {comp}")
                        builder.add_line(f"&& {comparisons[-1]};")
        builder.add_line("}")

        builder.add_line()
        builder.add_line(f"/// Inequality comparison")
        builder.add_line(f"bool operator!=(const {type_info.name}& other) const {{")
        with builder:
            builder.add_line("return !(*this == other);")
        builder.add_line("}")

    def _write_serialization_methods(
        self,
        type_info: TypeInfo,
        builder: CodeBuilder
    ):
        """Write serialization method declarations."""
        builder.add_line("/// Serialize to binary buffer")
        builder.add_line("void serialize(std::vector<uint8_t>& buffer) const;")
        builder.add_line()
        builder.add_line("/// Deserialize from binary buffer")
        builder.add_line(f"static {type_info.name} deserialize(")
        with builder:
            builder.add_line("const uint8_t* data,")
            builder.add_line("size_t size);")
        builder.add_line()
        builder.add_line("/// Get serialized size in bytes")
        builder.add_line("size_t serialized_size() const;")
```

---

## Module: `enum_writer.py`

**Purpose**: Generate enum definitions

```python
class EnumWriter:
    """Generates C++ enum class code."""

    def __init__(self, type_mapper: TypeMapper, config: GeneratorConfig):
        self.type_mapper = type_mapper
        self.config = config

    def write_enum(
        self,
        type_info: TypeInfo,
        builder: CodeBuilder
    ):
        """Write enum class definition."""
        storage_type = type_info.enum_storage_type
        cpp_storage = self.type_mapper.PRIMITIVE_TYPES.get(storage_type, "int32_t")

        # Doc comment
        if self.config.generate_docs:
            builder.add_line(f"/// Enum {type_info.name}")

        # Enum declaration
        builder.add_line(f"enum class {type_info.name} : {cpp_storage} {{")

        with builder:
            # Members
            for i, member in enumerate(type_info.enum_members):
                comma = "," if i < len(type_info.enum_members) - 1 else ""
                builder.add_line(f"{member.name} = {member.value}{comma}")

        builder.add_line("};")

        # String conversion functions
        if self.config.generate_enum_strings:
            builder.add_line()
            self._write_to_string(type_info, builder)
            builder.add_line()
            self._write_from_string(type_info, builder)

    def _write_to_string(self, type_info: TypeInfo, builder: CodeBuilder):
        """Write enum to string conversion."""
        builder.add_line(f"/// Convert {type_info.name} to string")
        builder.add_line(f"inline const char* to_string({type_info.name} value) {{")
        with builder:
            builder.add_line("switch (value) {")
            with builder:
                for member in type_info.enum_members:
                    builder.add_line(f"case {type_info.name}::{member.name}:")
                    with builder:
                        builder.add_line(f'return "{member.name}";')
            builder.add_line("}")
            builder.add_line('return "UNKNOWN";')
        builder.add_line("}")

    def _write_from_string(self, type_info: TypeInfo, builder: CodeBuilder):
        """Write string to enum conversion."""
        builder.add_line(f"/// Convert string to {type_info.name}")
        builder.add_line(f"inline {type_info.name} {type_info.name.lower()}_from_string(const char* str) {{")
        with builder:
            for i, member in enumerate(type_info.enum_members):
                if_word = "if" if i == 0 else "else if"
                builder.add_line(f'{if_word} (std::strcmp(str, "{member.name}") == 0) {{')
                with builder:
                    builder.add_line(f"return {type_info.name}::{member.name};")
                builder.add_line("}")
            builder.add_line(f"// Default to first value")
            builder.add_line(f"return {type_info.name}::{type_info.enum_members[0].name};")
        builder.add_line("}")
```

---

## Module: `generator.py` - Main Orchestrator

**Purpose**: Coordinate code generation

```python
class CppGenerator:
    """Main C++ code generator."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.type_mapper = TypeMapper(config)
        self.struct_writer = StructWriter(self.type_mapper, config)
        self.enum_writer = EnumWriter(self.type_mapper, config)

    def generate_from_validation_result(
        self,
        result: ValidationResult,
        output_dir: Path
    ) -> GenerationResult:
        """Generate C++ code from validated IDL."""
        generated_files = []
        errors = []

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate header for each IDL file
        for file_path, file_info in result.parsed_files.items():
            try:
                cpp_file = self.generate_file(file_info, output_dir)
                generated_files.append(cpp_file)
            except Exception as e:
                errors.append(GenerationError(
                    file_path=file_path,
                    message=str(e),
                    error_type="generation_failed"
                ))

        return GenerationResult(
            success=len(errors) == 0,
            files=generated_files,
            errors=errors
        )

    def generate_file(self, file_info: FileInfo, output_dir: Path) -> Path:
        """Generate C++ header for one IDL file."""
        # Convert IDL path to C++ header path
        # common/geometry.msg → common/geometry.h
        cpp_path = output_dir / file_info.path.with_suffix('.h')
        cpp_path.parent.mkdir(parents=True, exist_ok=True)

        # Build the header
        builder = CodeBuilder()

        # Header guard or pragma once
        if self.config.use_pragma_once:
            builder.add_line("#pragma once")
        else:
            guard = self._make_header_guard(cpp_path, output_dir)
            builder.add_line(f"#ifndef {guard}")
            builder.add_line(f"#define {guard}")

        builder.add_line()

        # Includes
        includes = self._collect_includes(file_info)
        for include in sorted(includes):
            builder.add_line(f"#include {include}")

        builder.add_line()

        # Namespace opening
        namespaces = self._get_namespaces(file_info)
        for ns in namespaces:
            builder.add_line(f"namespace {ns} {{")

        builder.add_line()

        # Type aliases
        for alias in file_info.defined_aliases:
            cpp_target = self.type_mapper.PRIMITIVE_TYPES[alias.target_type]
            builder.add_line(f"using {alias.name} = {cpp_target};")
            builder.add_line()

        # Enums
        for type_info in file_info.defined_types:
            if type_info.kind == "enum":
                self.enum_writer.write_enum(type_info, builder)
                builder.add_line()

        # Structs
        for type_info in file_info.defined_types:
            if type_info.kind == "struct":
                self.struct_writer.write_struct(type_info, builder, file_info)
                builder.add_line()

        # Namespace closing
        for ns in reversed(namespaces):
            builder.add_line(f"}}  // namespace {ns}")

        # Header guard end
        if not self.config.use_pragma_once:
            builder.add_line()
            builder.add_line(f"#endif  // {guard}")

        # Write to file
        cpp_path.write_text(builder.build())

        return cpp_path

    def _make_header_guard(self, header_path: Path, base_dir: Path) -> str:
        """
        Generate header guard macro.

        Example: common/geometry.h → LUMOS_COMMON_GEOMETRY_H_
        """
        rel_path = header_path.relative_to(base_dir)
        guard = str(rel_path).replace('/', '_').replace('.', '_').upper()
        if self.config.namespace_prefix:
            guard = f"{self.config.namespace_prefix.upper()}_{guard}"
        guard += "_"
        return guard

    def _get_namespaces(self, file_info: FileInfo) -> List[str]:
        """Get namespace hierarchy for file."""
        parts = file_info.namespace.split("::")
        if self.config.namespace_prefix:
            parts.insert(0, self.config.namespace_prefix)
        return parts

    def _collect_includes(self, file_info: FileInfo) -> Set[str]:
        """Collect all required includes for file."""
        includes = set()

        # Standard includes
        includes.add("<cstdint>")

        # Collect from all fields
        for type_info in file_info.defined_types:
            for field in type_info.fields:
                cpp_type = self.type_mapper.to_cpp_type(field, file_info)
                includes.update(cpp_type.includes)

        # Includes from imports
        for import_path in file_info.imports:
            # Convert import to #include
            include_path = import_path.replace('/', '/') + ".h"
            includes.add(f'"{include_path}"')

        return includes
```

---

## Configuration

```python
@dataclass
class GeneratorConfig:
    """Configuration for C++ generation."""
    # Namespaces
    namespace_prefix: str = "lumos"

    # Header guards
    use_pragma_once: bool = True

    # Features
    generate_equality: bool = True
    generate_serialization: bool = False
    generate_docs: bool = True
    generate_enum_strings: bool = True
```

---

## Summary: Direct vs Template-Based

**Direct String Building (This Approach):**
- ✅ Simpler - no extra dependencies
- ✅ Easier to debug - see exactly what's generated
- ✅ More flexible - Python logic directly in code
- ✅ Better IDE support - no template syntax highlighting issues
- ❌ Code can get verbose for complex generation
- ❌ Harder for non-programmers to customize

**Jinja2 Templates:**
- ✅ Clean separation of logic and presentation
- ✅ Easier for non-programmers to edit
- ✅ Template inheritance/includes
- ❌ Extra dependency
- ❌ Less flexible for complex logic
- ❌ Debugging is harder (template errors)

**Recommendation**: Start with direct building. Add Jinja2 later if:
- Templates become too complex
- Non-programmers need to customize output
- You want template inheritance

The `CodeBuilder` helper class gives you most of the benefits of templates without the complexity.
