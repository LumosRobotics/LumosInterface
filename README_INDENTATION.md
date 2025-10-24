# Indentation Preprocessing for LumosInterface IDL

## Overview

LumosInterface uses **indentation-sensitive syntax** for struct and field attributes, similar to Python. However, the Lark parser with LALR doesn't natively support indentation-based parsing.

**Solution**: A **preprocessing step** converts indentation into explicit `<INDENT>` and `<DEDENT>` markers that the grammar can parse.

## How It Works

### 1. Original IDL Code (Indentation-based)

```
struct Position
    [attributes]
        packed: true
        version: "1.0"
    float64 lat
        description: "Latitude"
        unit: "deg"
    float64 lon
```

### 2. After Preprocessing (Markers added)

```
struct Position
<INDENT>
[attributes]
<INDENT>
packed: true
version: "1.0"
<DEDENT>
float64 lat
<INDENT>
description: "Latitude"
unit: "deg"
<DEDENT>
float64 lon
<DEDENT>
```

### 3. Grammar Parses Markers

```lark
struct_def: "struct" CNAME NEWLINE INDENT struct_body DEDENT

struct_body: struct_attributes? struct_field+

struct_attributes: "[" "attributes" "]" NEWLINE INDENT attribute_entry+ DEDENT

struct_field: primitive_type CNAME NEWLINE field_attributes?

field_attributes: INDENT attribute_entry+ DEDENT
```

## Usage

### In Your Code

```python
from lark import Lark
from indentation_preprocessor import IndentationPreprocessor

# Load grammar
with open('grammar/message.lark') as f:
    grammar = f.read()

parser = Lark(grammar, parser='lalr', start='start')
preprocessor = IndentationPreprocessor()

# Parse IDL code
with open('my_interface.msg') as f:
    code = f.read()

# Preprocess indentation
processed_code = preprocessor.process(code)

# Parse
tree = parser.parse(processed_code)
```

### Indentation Rules

1. **4 spaces per indentation level** (default, configurable)
2. **Tabs are converted** to spaces (tab_size=4 by default)
3. **Empty lines** and **comment-only lines** are preserved as-is
4. **Consistent indentation** is required (Python-like rules)

### Example: Struct with Attributes

```
struct Position
    [attributes]           # Struct attributes block
        packed: true       # Indented under [attributes]
        aligned: 8
    float64 lat           # Field (same level as [attributes])
        description: "..."  # Field attribute (indented under field)
        unit: "deg"
    float64 lon           # Another field
```

**Indentation levels:**
- Struct body: 4 spaces
- [attributes] block: 4 spaces
- Attribute entries: 8 spaces
- Fields: 4 spaces
- Field attributes: 8 spaces

## Multiline Strings

Field and struct attributes support multiline strings using triple quotes:

```
struct SensorData
    float32 temperature
        description: """Temperature measurement
        Range: -40 to 85°C
        Accuracy: ±0.5°C"""
        unit: "celsius"
```

**Features:**
- Triple quotes `"""` for multiline strings
- Indentation inside strings is preserved
- Can contain quotes, newlines, and special characters
- Works in both field attributes and struct `[attributes]` blocks

## Benefits

✅ **Clean syntax** - No explicit markers in source files
✅ **Python-like** - Familiar indentation rules
✅ **Multiline strings** - Triple-quoted strings with preserved indentation
✅ **Unambiguous** - Indentation clearly shows structure
✅ **Compatible with LALR** - Works with standard parsers
✅ **Simple preprocessing** - ~150 lines of Python code

## Implementation

See `indentation_preprocessor.py` for the full implementation.

### Key Features

- **Stack-based** indentation tracking
- **Error reporting** for inconsistent indentation
- **Tab handling** with configurable tab size
- **Comment preservation** - Comments aren't affected
- **Empty line handling** - Blank lines ignored

## Testing

All struct tests use the preprocessor:

```bash
python3.9 test_struct_standalone.py
# Results: 16/16 tests passed ✓
```

Tests cover:
- Struct attributes
- Field attributes
- Mixed indentation levels
- User-defined types
- Error cases
