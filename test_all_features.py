#!/usr/bin/env python3.9
"""
Comprehensive test for all IDL features together.
"""

from lark import Lark
from pathlib import Path


def load_parser():
    """Load the grammar file and create parser."""
    grammar_file = Path("grammar/message.lark")

    with open(grammar_file) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


def main():
    """Test all features together."""
    parser = load_parser()

    print("=" * 70)
    print("Comprehensive IDL Feature Test")
    print("=" * 70)
    print()

    # Comprehensive example with all features
    code = """// Comprehensive IDL example demonstrating all features
import common/geometry
import sensors/gps

// Type aliases for convenience
using Timestamp = uint64
using GPSCoordinate = float64
using DeviceId = uint32
using Temperature = float32
using Pressure = float32

// Physical constants
const uint8 MAX_SATELLITES = 12
const float32 EARTH_RADIUS_M = 6371000.0
const uint8 VERSION = 1
const float64 GRAVITY = 9.81

// More imports
import common/constants
"""

    try:
        tree = parser.parse(code)

        imports = list(tree.find_data('import_stmt'))
        aliases = list(tree.find_data('using_def'))
        constants = list(tree.find_data('const_def'))

        print("Feature Summary:")
        print("-" * 70)
        print(f"✓ Imports:      {len(imports)} statements")
        print(f"✓ Type aliases: {len(aliases)} definitions")
        print(f"✓ Constants:    {len(constants)} definitions")
        print()

        print("Parsed successfully!")
        print("-" * 70)

        # Show import details
        print("\nImports:")
        for imp in imports:
            path = imp.children[0].value
            print(f"  - {path}")

        # Show alias details
        print("\nType Aliases:")
        for alias in aliases:
            name = alias.children[0].value
            type_val = alias.children[1].children[0].value
            print(f"  - {name} = {type_val}")

        # Show constant details
        print("\nConstants:")
        for const in constants:
            name = const.children[1].value
            type_val = const.children[0].children[0].value
            value = const.children[2].children[0].value
            print(f"  - {name}: {type_val} = {value}")

        print()
        print("=" * 70)
        print("✓ All features work correctly together!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
