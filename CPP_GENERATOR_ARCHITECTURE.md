# C++ Code Generator Architecture

## Overview

This document outlines the architecture for generating C++ code from validated LumosInterface IDL files. The generator produces header files (.h) with struct/class definitions, serialization support, and optional ROS2 integration.

---

## Design Goals

1. **Type Safety**: Generate strongly-typed C++ code
2. **Zero-Copy**: Support efficient memory operations where possible
3. **Serialization**: Built-in support for binary serialization
4. **Interoperability**: Optional ROS2 message compatibility
5. **Modern C++**: Use C++17 features (std::optional, std::variant, etc.)
6. **Header-Only**: Generate header-only code for ease of use
7. **Namespace Mapping**: IDL namespaces → C++ namespaces
8. **Documentation**: Generate Doxygen comments from IDL

---

## Architecture Components

```
generator/
├── cpp_generator.py           # Main generator orchestrator
├── type_mapper.py             # IDL type → C++ type mapping
├── struct_generator.py        # Generate struct/class definitions
├── enum_generator.py          # Generate enum definitions
├── serialization_generator.py # Generate serialization code
├── template_engine.py         # Template-based code generation
└── templates/
    ├── struct.h.jinja2        # Struct template
    ├── enum.h.jinja2          # Enum template
    ├── serialization.h.jinja2 # Serialization template
    └── interface.h.jinja2     # Interface (abstract base) template
```

---

## Module Specifications

### 1. `cpp_generator.py` - Main Orchestrator

**Purpose**: Coordinate code generation from validated IDL

```python
class CppGenerator:
    """Main C++ code generator."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.type_mapper = TypeMapper(config)
        self.struct_gen = StructGenerator(config)
        self.enum_gen = EnumGenerator(config)
        self.serialization_gen = SerializationGenerator(config)
        self.template_engine = TemplateEngine()

    def generate_from_validation_result(
        self,
        result: ValidationResult,
        output_dir: Path
    ) -> GenerationResult:
        """
        Generate C++ code from validated IDL.

        Process:
        1. Create output directory structure (mirrors IDL structure)
        2. Generate enum headers
        3. Generate struct headers
        4. Generate interface headers
        5. Generate serialization utilities
        6. Generate CMakeLists.txt (optional)

        Returns:
            GenerationResult with list of generated files
        """

    def generate_file(self, file_info: FileInfo, output_dir: Path) -> List[Path]:
        """
        Generate C++ header for a single IDL file.

        IDL: common/geometry.msg
        C++: common/geometry.h

        Returns list of generated files (may include multiple if split)
        """

    def generate_header_guards(self, file_path: Path) -> str:
        """
        Generate header guard macros.

        Example: common/geometry.h → LUMOS_COMMON_GEOMETRY_H_
        """

    def generate_includes(self, file_info: FileInfo) -> List[str]:
        """
        Generate #include directives based on dependencies.

        - Import statements → #include "other/file.h"
        - Primitive types → <cstdint>, <string>, etc.
        - Collections → <array>, <vector>
        """
```

---

### 2. `type_mapper.py` - Type Mapping

**Purpose**: Map IDL types to C++ types

```python
class TypeMapper:
    """Maps IDL types to C++ types."""

    # Primitive type mappings
    PRIMITIVE_MAP = {
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

    def map_type(self, type_name: str, context: FileInfo) -> CppType:
        """
        Map IDL type to C++ type.

        Returns CppType with:
        - cpp_type: The C++ type string
        - includes: Required #include directives
        - is_primitive: Whether it's a primitive type
        """

    def map_collection(self, collection_info: CollectionInfo) -> CppType:
        """
        Map collection types to C++.

        Examples:
        - array<float32, 3> → std::array<float, 3>
        - array<float32, ?> → std::vector<float>
        - array<float32, max=100> → std::vector<float> (with validation)
        - matrix<float32, 3, 3> → std::array<std::array<float, 3>, 3>
        - tensor<float32, 2, 3, 4> → std::array<std::array<std::array<float, 4>, 3>, 2>
        """

    def map_enum(self, enum_info: TypeInfo) -> CppType:
        """
        Map enum to C++ enum class.

        IDL:
          enum Status : uint32
            OK = 0
            ERROR = 1

        C++:
          enum class Status : uint32_t {
            OK = 0,
            ERROR = 1
          };
        """

    def map_alias(self, alias_info: AliasInfo) -> str:
        """
        Map type alias to C++ using.

        IDL:
          using Timestamp = uint64

        C++:
          using Timestamp = uint64_t;
        """

    def map_optional(self, type_name: str) -> CppType:
        """
        Map optional fields to std::optional.

        IDL:
          optional string description

        C++:
          std::optional<std::string> description;
        """

@dataclass
class CppType:
    """Represents a C++ type with metadata."""
    cpp_type: str                    # The C++ type string
    includes: List[str]              # Required includes
    is_primitive: bool = False       # Is this a primitive type?
    needs_forward_decl: bool = False # Needs forward declaration?
    namespace_prefix: str = ""       # Namespace prefix if needed
```

---

### 3. `struct_generator.py` - Struct Generation

**Purpose**: Generate C++ struct/class definitions

```python
class StructGenerator:
    """Generates C++ struct definitions."""

    def generate_struct(self, type_info: TypeInfo) -> str:
        """
        Generate C++ struct from IDL struct.

        IDL:
          struct Vector3
            float32 x
            float32 y
            float32 z

        C++:
          struct Vector3 {
            float x;
            float y;
            float z;

            // Default constructor
            Vector3() = default;

            // Constructor with values
            Vector3(float x_, float y_, float z_)
              : x(x_), y(y_), z(z_) {}

            // Equality operators
            bool operator==(const Vector3& other) const;
            bool operator!=(const Vector3& other) const;
          };
        """

    def generate_field(self, field_info: FieldInfo) -> str:
        """
        Generate field declaration.

        Examples:
        - float32 x → float x;
        - optional string name → std::optional<std::string> name;
        - array<float32, 3> values → std::array<float, 3> values;
        """

    def generate_constructor(self, type_info: TypeInfo) -> str:
        """
        Generate constructors.

        Options:
        1. Default constructor
        2. Value constructor (all fields)
        3. Builder pattern (for complex structs)
        """

    def generate_comparison_operators(self, type_info: TypeInfo) -> str:
        """
        Generate operator== and operator!=.

        Compares all fields for equality.
        """

    def generate_accessors(
        self,
        type_info: TypeInfo,
        style: str = "direct"  # "direct" or "getters"
    ) -> str:
        """
        Generate field accessors.

        direct: Public fields (default)
        getters: Private fields with get/set methods
        """
```

---

### 4. `enum_generator.py` - Enum Generation

**Purpose**: Generate C++ enum class definitions

```python
class EnumGenerator:
    """Generates C++ enum class definitions."""

    def generate_enum(self, type_info: TypeInfo) -> str:
        """
        Generate C++ enum class.

        IDL:
          enum Status : uint32
            OK = 0
            ERROR = 1
            WARNING = 2

        C++:
          enum class Status : uint32_t {
            OK = 0,
            ERROR = 1,
            WARNING = 2
          };

          // String conversion
          inline const char* to_string(Status value);
          inline Status status_from_string(const char* str);
        """

    def generate_string_conversion(self, type_info: TypeInfo) -> str:
        """
        Generate enum ↔ string conversion functions.

        Useful for debugging, logging, serialization.
        """

    def generate_enum_traits(self, type_info: TypeInfo) -> str:
        """
        Generate enum traits for metaprogramming.

        template<>
        struct enum_traits<Status> {
          static constexpr size_t count = 3;
          static constexpr Status min = Status::OK;
          static constexpr Status max = Status::WARNING;
        };
        """
```

---

### 5. `serialization_generator.py` - Serialization

**Purpose**: Generate binary serialization code

```python
class SerializationGenerator:
    """Generates serialization/deserialization code."""

    def generate_serialize(self, type_info: TypeInfo) -> str:
        """
        Generate serialize() method.

        Options:
        1. Binary (native endianness)
        2. Network byte order (big-endian)
        3. Protocol Buffers compatible
        4. MessagePack
        """

    def generate_deserialize(self, type_info: TypeInfo) -> str:
        """
        Generate deserialize() method.

        Must handle:
        - Endianness conversion
        - Version compatibility (if field numbers used)
        - Error handling (buffer too small, invalid data)
        """

    def generate_size_calculation(self, type_info: TypeInfo) -> str:
        """
        Generate serialized_size() method.

        Returns size in bytes for serialization buffer allocation.

        For dynamic types (strings, vectors), size depends on content.
        For fixed types (primitives, arrays), size is constant.
        """
```

**Serialization Format Options:**

```cpp
// Option 1: Simple binary (native endianness)
struct Vector3 {
  float x, y, z;

  void serialize(std::vector<uint8_t>& buffer) const {
    size_t offset = buffer.size();
    buffer.resize(offset + sizeof(*this));
    std::memcpy(buffer.data() + offset, this, sizeof(*this));
  }
};

// Option 2: Field-by-field with field numbers (Protocol Buffers style)
struct Vector3 {
  float x;  // field 0
  float y;  // field 1
  float z;  // field 2

  void serialize(std::vector<uint8_t>& buffer) const {
    serialize_field(buffer, 0, x);
    serialize_field(buffer, 1, y);
    serialize_field(buffer, 2, z);
  }

  static Vector3 deserialize(const uint8_t* data, size_t size) {
    Vector3 result;
    // Read fields by number (can skip unknown fields)
    while (/* has more data */) {
      auto [field_num, value] = read_field(data);
      switch (field_num) {
        case 0: result.x = value; break;
        case 1: result.y = value; break;
        case 2: result.z = value; break;
        default: /* skip unknown field */
      }
    }
    return result;
  }
};
```

---

### 6. `template_engine.py` - Templates

**Purpose**: Jinja2-based template rendering

```python
class TemplateEngine:
    """Renders C++ code from templates."""

    def __init__(self, template_dir: Path):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Custom filters for C++ generation
        self.env.filters['cpp_type'] = self.to_cpp_type
        self.env.filters['header_guard'] = self.to_header_guard
        self.env.filters['namespace'] = self.to_namespace

    def render_struct(self, type_info: TypeInfo, context: dict) -> str:
        """Render struct template."""

    def render_enum(self, type_info: TypeInfo, context: dict) -> str:
        """Render enum template."""
```

**Template Example** (`struct.h.jinja2`):

```cpp
// Generated from {{ source_file }}
// DO NOT EDIT - Generated code

#ifndef {{ header_guard }}
#define {{ header_guard }}

{% for include in includes %}
#include {{ include }}
{% endfor %}

{% for ns in namespaces %}
namespace {{ ns }} {
{% endfor %}

/// {{ doc_comment }}
struct {{ struct_name }} {
  {% for field in fields %}
  {{ field.cpp_type }} {{ field.name }};  ///< {{ field.description }}
  {% endfor %}

  // Default constructor
  {{ struct_name }}() = default;

  // Value constructor
  {{ struct_name }}(
    {% for field in fields %}
    {{ field.cpp_type }} {{ field.name }}_{{ "," if not loop.last }}
    {% endfor %}
  ) : {% for field in fields %}{{ field.name }}({{ field.name }}_){{ "," if not loop.last }}{% endfor %} {}

  // Equality operators
  bool operator==(const {{ struct_name }}& other) const {
    return {% for field in fields %}{{ field.name }} == other.{{ field.name }}{{ " &&" if not loop.last }}{% endfor %};
  }

  bool operator!=(const {{ struct_name }}& other) const {
    return !(*this == other);
  }

  {% if with_serialization %}
  // Serialization
  void serialize(std::vector<uint8_t>& buffer) const;
  static {{ struct_name }} deserialize(const uint8_t* data, size_t size);
  size_t serialized_size() const;
  {% endif %}
};

{% for ns in namespaces|reverse %}
}  // namespace {{ ns }}
{% endfor %}

#endif  // {{ header_guard }}
```

---

## Configuration

```python
@dataclass
class GeneratorConfig:
    """Configuration for C++ code generation."""

    # Output options
    output_dir: Path
    namespace_prefix: str = "lumos"  # Root namespace

    # Code style
    use_pragma_once: bool = False    # Use #pragma once vs header guards
    field_naming: str = "snake_case" # snake_case or camelCase
    generate_getters: bool = False   # Generate get/set methods

    # Features
    generate_serialization: bool = True
    serialization_format: str = "binary"  # binary, protobuf, msgpack
    generate_equality: bool = True
    generate_comparison: bool = False     # operator<, etc.

    # ROS2 integration
    generate_ros2_msgs: bool = False
    ros2_package_name: str = ""

    # Documentation
    generate_docs: bool = True
    doc_format: str = "doxygen"  # doxygen, javadoc

    # Dependencies
    include_paths: List[Path] = field(default_factory=list)

    # Advanced
    generate_cmake: bool = True
    split_per_type: bool = False  # One file per type vs one per IDL file
```

---

## Usage Example

```python
from lumos_idl import IDLProcessor
from lumos_idl.generator.cpp_generator import CppGenerator, GeneratorConfig
from pathlib import Path

# 1. Validate IDL files
processor = IDLProcessor()
result = processor.process_file("interfaces/robot_state.msg")

if not result.success:
    print("Validation failed!")
    result.print_errors()
    exit(1)

# 2. Configure generator
config = GeneratorConfig(
    output_dir=Path("generated/cpp"),
    namespace_prefix="lumos",
    generate_serialization=True,
    serialization_format="binary",
    generate_cmake=True,
)

# 3. Generate C++ code
generator = CppGenerator(config)
gen_result = generator.generate_from_validation_result(result, config.output_dir)

# 4. Report results
print(f"Generated {len(gen_result.files)} files:")
for file in gen_result.files:
    print(f"  - {file}")
```

---

## Generated File Structure

```
generated/cpp/
├── CMakeLists.txt              # Build configuration
├── common/
│   ├── geometry.h              # From common/geometry.msg
│   │   ├── Vector3 struct
│   │   ├── Quaternion struct
│   │   └── Transform struct
│   └── types.h                 # From common/types.msg
├── interfaces/
│   ├── robot_state.h           # From interfaces/robot_state.msg
│   └── sensor_data.h           # From interfaces/sensor_data.msg
└── lumos/                      # Utilities
    ├── serialization.h         # Serialization helpers
    └── traits.h                # Type traits
```

---

## Interface (Abstract Base Class) Handling

IDL interfaces should generate C++ abstract base classes:

**IDL:**
```
interface SensorInterface
    uint32 get_sensor_id()
    float64 read_value()
```

**Generated C++:**
```cpp
class SensorInterface {
public:
  virtual ~SensorInterface() = default;

  virtual uint32_t get_sensor_id() const = 0;
  virtual double read_value() const = 0;
};

// Concrete implementation example
class ConcreteSensor : public SensorInterface {
public:
  uint32_t get_sensor_id() const override { return sensor_id_; }
  double read_value() const override { return value_; }

private:
  uint32_t sensor_id_;
  double value_;
};
```

---

## ROS2 Integration (Optional)

If `generate_ros2_msgs = True`, generate ROS2 message files:

**IDL:**
```
struct Vector3
    float64 x
    float64 y
    float64 z
```

**Generated ROS2 (.msg):**
```
# Generated from LumosInterface IDL
float64 x
float64 y
float64 z
```

**Generated ROS2 Conversion:**
```cpp
// Convert between Lumos and ROS2 types
inline lumos::Vector3 from_ros(const geometry_msgs::msg::Vector3& ros_msg) {
  return {ros_msg.x, ros_msg.y, ros_msg.z};
}

inline geometry_msgs::msg::Vector3 to_ros(const lumos::Vector3& lumos_msg) {
  geometry_msgs::msg::Vector3 result;
  result.x = lumos_msg.x;
  result.y = lumos_msg.y;
  result.z = lumos_msg.z;
  return result;
}
```

---

## Error Handling

```python
@dataclass
class GenerationError:
    """Error during code generation."""
    file_path: Path
    message: str
    error_type: str  # "unsupported_type", "circular_dependency", etc.

@dataclass
class GenerationResult:
    """Result of code generation."""
    success: bool
    files: List[Path]               # Generated files
    errors: List[GenerationError]
    warnings: List[str]

    def print_summary(self):
        """Print generation summary."""
```

---

## Testing Strategy

### Unit Tests
- Test type mapping for all primitive types
- Test collection mapping (array, matrix, tensor)
- Test namespace handling
- Test include generation

### Integration Tests
- Generate code from real IDL files
- Compile generated code with C++ compiler
- Test serialization round-trip (serialize → deserialize → compare)
- Test ROS2 conversion (if enabled)

### Golden Files
- Store expected generated code for regression testing
- Compare generated output against golden files

---

## Future Enhancements

1. **Reflection/Introspection**: Generate type metadata for runtime reflection
2. **JSON Support**: Generate JSON serialization (nlohmann::json)
3. **Memory Pools**: Generate custom allocators for zero-copy
4. **Validation**: Generate runtime validation for field constraints
5. **Python Bindings**: Generate pybind11 bindings automatically
6. **Code Formatting**: Integrate clang-format for consistent style
7. **Documentation**: Generate HTML docs with cross-references

---

## Dependencies

**Required:**
- Python 3.9+
- Jinja2 (template engine)

**Optional:**
- clang-format (code formatting)
- Doxygen (documentation generation)
- CMake (build system generation)

---

## Performance Considerations

1. **Fixed-Size Structs**: Use `std::array` for fixed collections (stack allocation)
2. **Dynamic Strings**: Use `std::string` with SSO (Small String Optimization)
3. **Optional Fields**: `std::optional` has minimal overhead for primitives
4. **Serialization**: Provide both buffered and streaming serialization
5. **Zero-Copy**: Support direct memory mapping for large data

---

## Summary

The C++ generator transforms validated IDL into production-ready C++ code with:
- Strong type safety
- Efficient serialization
- Modern C++ idioms
- Optional ROS2 integration
- Comprehensive testing

The modular architecture allows customization of generated code style, features, and target environment.
