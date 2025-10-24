# LumosInterface Validation Architecture

## Overview

This document defines the architecture for semantic validation of LumosInterface IDL files. The grammar handles syntax validation; this validator handles semantic rules.

---

## Phase 1: Parsing (Already Complete)

**Input:** `.msg` files
**Output:** Lark AST
**Components:**
- `grammar/message.lark` - Grammar definition
- `indentation_preprocessor.py` - Converts indentation to tokens
- Lark parser - Generates AST

**What it validates:**
- ✅ Syntax correctness
- ✅ Token matching
- ✅ Structure rules (e.g., fields need types and names)

**What it CANNOT validate:**
- ❌ Type references exist
- ❌ Import paths are valid
- ❌ Field numbers are unique
- ❌ Namespace resolution
- ❌ Circular dependencies

---

## Phase 2: Semantic Validation (To Implement)

### Architecture Components

```
validator.py                    # Main validator orchestrator
├── symbol_table.py            # Symbol table and scope management
├── import_resolver.py         # Import path resolution
├── type_checker.py            # Type reference validation
├── field_validator.py         # Field-specific validation
└── error_reporter.py          # Error collection and reporting
```

---

## Module Specifications

### 1. `symbol_table.py`

**Purpose:** Track all defined types, their locations, and visibility

**Classes:**

```python
class SymbolTable:
    """Central registry of all types and their definitions."""

    def __init__(self):
        self.types: Dict[str, TypeInfo] = {}          # Fully qualified name -> TypeInfo
        self.files: Dict[Path, FileInfo] = {}         # File -> FileInfo
        self.aliases: Dict[str, str] = {}             # Alias -> Full name

    def register_type(self, fq_name: str, type_info: TypeInfo)
    def lookup_type(self, name: str, context: FileInfo) -> Optional[TypeInfo]
    def resolve_type(self, name: str, using_namespaces: List[str]) -> Optional[str]
    def register_namespace_alias(self, alias: str, namespace: str)

class TypeInfo:
    """Information about a defined type."""
    name: str                    # Simple name (e.g., "Position")
    qualified_name: str          # Full name (e.g., "common::geometry::Position")
    kind: str                    # "struct", "interface", "enum"
    file_path: Path              # Where it's defined
    ast_node: Tree               # AST node reference
    fields: List[FieldInfo]      # Fields (for struct/interface)

class FileInfo:
    """Information about a parsed file."""
    path: Path
    namespace: str               # Derived from path (e.g., "common::geometry")
    imports: List[str]           # Import paths
    using_namespaces: List[str]  # "using namespace X" statements
    namespace_aliases: Dict[str, str]  # "namespace x = y" statements
    defined_types: Set[str]      # Types defined in this file
    ast: Tree                    # Parsed AST

class FieldInfo:
    """Information about a struct/interface field."""
    name: str
    type_name: str               # Type reference (may be unresolved)
    field_number: Optional[int]  # Field number (if specified)
    optional: bool
    line_number: int
```

---

### 2. `import_resolver.py`

**Purpose:** Resolve import statements to actual file paths

**Classes:**

```python
class ImportResolver:
    """Resolves import paths to file paths."""

    def __init__(self, search_paths: List[Path]):
        self.search_paths = search_paths  # Base directories to search
        self.cache: Dict[str, Path] = {}  # Cache resolved paths

    def resolve_import(self, import_path: str) -> Optional[Path]:
        """
        Convert import path to file path.

        Examples:
            "common/geometry" -> "<base>/common/geometry.msg"
            "common/geo.types" -> "<base>/common/geo.types.msg"

        Algorithm:
            1. Replace '/' with OS path separator
            2. Append '.msg' extension
            3. Search in each search_path
            4. Return first match or None
        """

    def extract_imports_from_ast(self, ast: Tree) -> List[str]:
        """Extract all import statements from AST."""
        # Find all "import_stmt" nodes
        # Extract import_path from each
        # Return list of import path strings

    def build_dependency_graph(self, files: Dict[Path, FileInfo]) -> Dict[Path, Set[Path]]:
        """Build file dependency graph."""
        # For each file, resolve its imports to file paths
        # Return adjacency list

    def detect_cycles(self, graph: Dict[Path, Set[Path]]) -> List[List[Path]]:
        """Detect circular dependencies using DFS."""
        # Return list of cycles (each cycle is list of paths)
```

---

### 3. `type_checker.py`

**Purpose:** Validate all type references

**Classes:**

```python
class TypeChecker:
    """Validates type references in fields."""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.primitive_types = {
            "bool", "int8", "int16", "int32", "int64",
            "uint8", "uint16", "uint32", "uint64",
            "float32", "float64", "string"
        }

    def check_type_reference(self, type_ref: str, context: FileInfo) -> ValidationResult:
        """
        Check if a type reference is valid.

        Algorithm:
            1. If primitive type -> valid
            2. If qualified (contains "::") -> lookup directly in symbol table
            3. If simple name:
               a. Check local file types
               b. Check using namespace imports
               c. Check namespace aliases
               d. Check imported file types
            4. Return result with error if not found
        """

    def validate_collection_element_type(self, element_type: str, context: FileInfo) -> ValidationResult:
        """Validate element type in array/matrix/tensor."""

    def validate_file_types(self, file_info: FileInfo) -> List[ValidationError]:
        """Validate all type references in a file."""
        # Walk AST
        # Check each field type
        # Check collection element types
        # Return list of errors

class ValidationResult:
    valid: bool
    resolved_type: Optional[str]  # Fully qualified name if resolved
    error: Optional[str]

class ValidationError:
    file: Path
    line: int
    column: int
    message: str
    error_type: str  # "type_not_found", "circular_import", etc.
```

---

### 4. `field_validator.py`

**Purpose:** Validate field-specific rules

**Classes:**

```python
class FieldValidator:
    """Validates struct/interface field constraints."""

    def validate_field_numbering(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate field numbering rules:
        1. All-or-nothing: if any field has number, all must have numbers
        2. Uniqueness: no duplicate numbers within struct
        3. Range: warn if negative or > 536870911 (protobuf limit)
        4. Gaps: warn about gaps (potential reserved numbers)
        """

    def validate_field_names(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate field name rules:
        1. Uniqueness: no duplicate field names
        2. Naming convention: optional warnings
        """

    def validate_optional_fields(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate optional field usage:
        1. Optional with field numbers (compatible)
        2. Optional primitive vs complex types
        """

    def validate_collection_sizes(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate collection size constraints:
        1. Fixed size > 0
        2. Max size > 0
        3. Matrix must have exactly 2 dimensions
        4. Tensor must have at least 1 dimension
        """

    def validate_attributes(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate field attributes:
        1. Valid attribute names (if restricted)
        2. Valid attribute values
        3. Conflicting attributes
        """
```

---

### 5. `error_reporter.py`

**Purpose:** Collect and format validation errors

**Classes:**

```python
class ErrorReporter:
    """Collects and formats validation errors."""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(self, error: ValidationError):
        """Add an error."""

    def add_warning(self, warning: ValidationError):
        """Add a warning."""

    def has_errors(self) -> bool:
        """Check if any errors were reported."""

    def format_report(self) -> str:
        """
        Format errors and warnings for display.

        Format:
            Error: type_not_found
              File: common/geometry.msg:15:5
              Message: Type 'Vector4' not found

            Warning: field_number_gap
              File: data.msg:23:5
              Message: Field number gap detected (1 -> 5). Consider reserving 2-4.
        """

    def print_report(self):
        """Print formatted report to stdout."""
```

---

### 6. `validator.py` (Main Orchestrator)

**Purpose:** Coordinate all validation phases

**Classes:**

```python
class IDLValidator:
    """Main validator orchestrator."""

    def __init__(self, search_paths: List[Path]):
        self.parser = load_parser()
        self.preprocessor = IndentationPreprocessor()
        self.import_resolver = ImportResolver(search_paths)
        self.symbol_table = SymbolTable()
        self.type_checker = TypeChecker(self.symbol_table)
        self.field_validator = FieldValidator()
        self.error_reporter = ErrorReporter()

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate a single IDL file and its dependencies.

        Returns: True if validation passed, False otherwise
        """
        # Phase 1: Parse and build symbol table
        files_to_parse = self._collect_files(file_path)
        for f in files_to_parse:
            self._parse_and_register(f)

        # Phase 2: Check imports and dependencies
        self._validate_imports()

        # Phase 3: Type checking
        self._validate_types()

        # Phase 4: Field validation
        self._validate_fields()

        # Phase 5: Report
        self.error_reporter.print_report()
        return not self.error_reporter.has_errors()

    def _collect_files(self, entry_point: Path) -> Set[Path]:
        """Recursively collect all files via imports."""
        # BFS through imports
        # Return set of all reachable files

    def _parse_and_register(self, file_path: Path):
        """Parse file and register types in symbol table."""
        # 1. Read file
        # 2. Preprocess indentation
        # 3. Parse with Lark
        # 4. Extract imports
        # 5. Extract type definitions (struct/interface)
        # 6. Register in symbol table

    def _validate_imports(self):
        """Validate all imports."""
        # 1. Resolve all import paths
        # 2. Check files exist
        # 3. Detect circular dependencies
        # 4. Report errors

    def _validate_types(self):
        """Validate all type references."""
        # For each file:
        #   For each field:
        #     Check type reference is valid

    def _validate_fields(self):
        """Validate field-specific rules."""
        # For each type:
        #   Validate field numbering
        #   Validate field names
        #   Validate attributes
```

---

## Validation Rules Summary

### Import Validation
- ✅ Import path resolves to existing file
- ✅ No circular imports
- ✅ Imported file is valid IDL

### Type Validation
- ✅ All type references exist (primitive or defined)
- ✅ Qualified types resolve correctly
- ✅ Namespace aliases resolve correctly
- ✅ `using namespace` imports work correctly
- ✅ Collection element types are valid

### Field Numbering Validation
- ✅ **All-or-nothing rule**: If any field in a struct has a number, all fields must have numbers
- ✅ **Uniqueness**: No duplicate field numbers within same struct/interface
- ✅ **Range**: Numbers should be >= 0 and <= 536870911 (optional warning for protobuf compatibility)
- ⚠️ **Gaps**: Warn about gaps (suggest reserved numbers)

### Field Name Validation
- ✅ **Uniqueness**: No duplicate field names within same struct/interface
- ⚠️ **Naming convention**: Optional warnings for style

### Collection Validation
- ✅ Fixed size must be > 0
- ✅ Max size must be > 0
- ✅ Matrix must have exactly 2 size specs
- ✅ Tensor must have at least 1 size spec
- ✅ Element type must be valid

### Attribute Validation
- ⚠️ Unknown attributes (if we maintain a whitelist)
- ✅ Attribute value types match expected types

### Struct/Interface Validation
- ✅ At least one field required
- ✅ No duplicate type names in same namespace
- ✅ No circular type dependencies (e.g., struct A contains field of type A)

---

## Error Severity Levels

```
ERROR   - Must be fixed, prevents code generation
WARNING - Should be reviewed, but not blocking
INFO    - Informational, best practices
```

---

## Usage Example

```python
from validator import IDLValidator
from pathlib import Path

# Create validator with search paths
validator = IDLValidator(search_paths=[
    Path("interfaces"),
    Path("common"),
])

# Validate a file
success = validator.validate_file(Path("interfaces/robot_state.msg"))

if success:
    print("✓ Validation passed")
else:
    print("✗ Validation failed")
    # Errors already printed by validator
```

---

## Implementation Order

### Phase 1: Foundation (First)
1. `error_reporter.py` - Error collection and formatting
2. `symbol_table.py` - Basic symbol table (without namespace resolution yet)
3. `validator.py` - Basic orchestrator (parse single file, no imports)

### Phase 2: Single File Validation (Second)
4. `field_validator.py` - Field numbering and name validation
5. Basic type checking (local types only, no imports)

### Phase 3: Multi-File Support (Third)
6. `import_resolver.py` - Import path resolution
7. Dependency graph and cycle detection
8. Cross-file type checking

### Phase 4: Advanced Features (Fourth)
9. `type_checker.py` - Full namespace resolution
10. Collection validation
11. Attribute validation

---

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock dependencies
- Cover edge cases

### Integration Tests
- Test with real `.msg` files
- Test cross-file imports
- Test error reporting

### Test Cases
1. **Valid cases**: Should pass validation
2. **Invalid cases**: Should report specific errors
3. **Edge cases**: Empty files, circular imports, complex namespaces

---

## Future Enhancements

- **Performance**: Cache parsed files, incremental validation
- **IDE Integration**: LSP server for real-time validation
- **Auto-fix**: Suggest fixes for common errors
- **Documentation generation**: Extract docs from validated AST
- **Code generation**: Generate code from validated AST (Python, C++, etc.)

---

## Notes

- This validator operates on the AST produced by Lark parser
- It assumes the grammar is correct and handles all syntax validation
- Focus is on **semantic** validation that requires multi-file analysis
- All file paths are relative to search_paths
- Namespace is derived from file path: `common/geometry.msg` → `common::geometry`
