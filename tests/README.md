# LumosInterface Test Suite

This directory contains comprehensive tests for the LumosInterface IDL parser and validator.

## Structure

```
tests/
├── test_parser.py          # Basic parsing tests
├── test_validation.py      # Semantic validation tests
└── test_files/
    ├── valid/              # Valid test cases that should parse successfully
    │   ├── basic_types.msg
    │   ├── arrays.msg
    │   ├── imports_*.msg
    │   ├── type_aliases.msg
    │   ├── attributes.msg
    │   └── interface.msg
    └── invalid/            # Invalid test cases that should fail
        ├── unknown_type.msg
        ├── missing_import.msg
        └── syntax_error.msg
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_parser.py
```

### Run specific test class
```bash
pytest tests/test_parser.py::TestBasicTypes
```

### Run specific test
```bash
pytest tests/test_parser.py::TestBasicTypes::test_parse_constants
```

### Run with verbose output
```bash
pytest -v
```

### Run with detailed output on failures
```bash
pytest -vv --tb=long
```

### Run only parser tests
```bash
pytest tests/test_parser.py
```

### Run only validation tests
```bash
pytest tests/test_validation.py
```

## Test Categories

### test_parser.py
- **TestParsing**: Basic parsing functionality
- **TestBasicTypes**: Constants, enums, structs, interfaces
- **TestAdvancedFeatures**: Comments, imports, type aliases
- **TestStructureValidation**: AST structure verification
- **TestArrays**: Array, matrix, tensor types
- **TestAttributes**: Struct and field attributes
- **TestPositionTracking**: Source location tracking
- **TestErrorMessages**: Error handling and messages
- **TestRealWorldExample**: Complex integration tests

### test_validation.py
- **TestTypeValidation**: Type checking and resolution
- **TestNamespaces**: Namespace generation and handling
- **TestConstants**: Constant definition validation
- **TestEnums**: Enum validation
- **TestStructs**: Struct validation
- **TestInterfaces**: Interface validation
- **TestFileOperations**: Multi-file parsing

## Adding New Tests

### 1. Add test file
Create a new `.msg` file in `test_files/valid/` or `test_files/invalid/`:

```
tests/test_files/valid/my_feature.msg
```

### 2. Add test case
Add a new test method to an existing test class or create a new one:

```python
def test_my_feature(self, parser):
    """Test my new feature."""
    code = """
    # Your IDL code here
    """
    tree = parser.parse(code.strip())
    assert tree is not None
```

## Test File Examples

### Valid Test File
```
// tests/test_files/valid/example.msg
const uint8 MAX = 100

struct Point
    float32 x
    float32 y
```

### Invalid Test File
```
// tests/test_files/invalid/bad_syntax.msg
struct Incomplete
    uint32
```

## Notes

- Tests are designed to be flexible and skip unsupported features gracefully
- If a feature is not yet implemented in the grammar, tests will skip with an appropriate message
- All tests expect `grammar/message.lark` to exist
- Tests track positions and line numbers for better error reporting

## Dependencies

Make sure you have pytest and lark installed:

```bash
pip install pytest lark
```
