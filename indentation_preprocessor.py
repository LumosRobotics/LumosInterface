"""
Indentation preprocessor for LumosInterface IDL.

Converts indentation-based structure into explicit INDENT/DEDENT markers
that can be parsed by a context-free grammar.
"""

from typing import List, Tuple


class IndentationPreprocessor:
    """Converts indentation to INDENT/DEDENT tokens."""

    def __init__(self, tab_size: int = 4):
        self.tab_size = tab_size

    def process(self, text: str) -> str:
        """
        Convert indentation-based structure to INDENT/DEDENT markers.

        Example:
            struct Point
                float32 x
                float32 y
                    description: "Y coordinate"

        Becomes:
            struct Point
            <INDENT>
            float32 x
            float32 y
            <INDENT>
            description: "Y coordinate"
            <DEDENT>
            <DEDENT>
        """
        lines = text.split('\n')
        processed_lines = []
        indent_stack = [0]  # Stack of indentation levels
        in_multiline_string = False
        multiline_start_indent = 0

        for i, line in enumerate(lines):
            stripped = line.lstrip()

            # Count triple quotes to detect multiline string boundaries
            triple_quote_count = line.count('"""')

            # Track if we were in a multiline string before processing this line
            was_in_multiline = in_multiline_string

            # Handle multiline string state transitions
            if triple_quote_count == 1:
                if not in_multiline_string:
                    # Starting a multiline string
                    in_multiline_string = True
                    multiline_start_indent = len(line) - len(stripped)
                    # Process this line normally (it contains the opening """)
                else:
                    # Ending a multiline string - preserve indentation on closing line
                    in_multiline_string = False
                    # This line has the closing """, preserve it as-is
                    processed_lines.append(line)
                    continue
            elif triple_quote_count == 2:
                # Single-line multiline string: """text"""
                # Process normally, don't change state
                pass

            # If we're inside a multiline string (between opening and closing """)
            # preserve the entire line with original indentation
            if was_in_multiline and in_multiline_string:
                processed_lines.append(line)
                continue

            # Skip empty lines and lines with only whitespace
            if not line.strip():
                processed_lines.append('')
                continue

            # Skip comment-only lines (preserve them as-is)
            if stripped.startswith('//') or stripped.startswith('/*'):
                processed_lines.append(line)
                continue

            # Calculate indentation level (number of spaces)
            indent_level = len(line) - len(stripped)

            # Convert tabs to spaces
            if '\t' in line[:indent_level]:
                # Count tabs and spaces
                tabs = line[:indent_level].count('\t')
                spaces = indent_level - tabs
                indent_level = tabs * self.tab_size + spaces

            current_indent = indent_stack[-1]

            if indent_level > current_indent:
                # Increased indentation - add INDENT
                indent_stack.append(indent_level)
                processed_lines.append('<INDENT>')
                processed_lines.append(stripped)

            elif indent_level < current_indent:
                # Decreased indentation - add DEDENT(s)
                while indent_stack and indent_stack[-1] > indent_level:
                    indent_stack.pop()
                    processed_lines.append('<DEDENT>')

                if not indent_stack or indent_stack[-1] != indent_level:
                    raise IndentationError(
                        f"Line {i+1}: Inconsistent indentation level {indent_level}"
                    )

                processed_lines.append(stripped)
            else:
                # Same indentation
                processed_lines.append(stripped)

        # Add final DEDENTs for any remaining indentation
        while len(indent_stack) > 1:
            indent_stack.pop()
            processed_lines.append('<DEDENT>')

        return '\n'.join(processed_lines)


def preprocess_file(filename: str) -> str:
    """Load a file and preprocess its indentation."""
    with open(filename, 'r') as f:
        content = f.read()

    preprocessor = IndentationPreprocessor()
    return preprocessor.process(content)


if __name__ == '__main__':
    # Test the preprocessor
    test_code = """struct Position
    [attributes]
        attribute0: true
        attribute2: "hello"
    float64 lat
        description: "Longitude in degrees"
        unit: "deg"
    float64 lon
"""

    preprocessor = IndentationPreprocessor()
    result = preprocessor.process(test_code)

    print("Original:")
    print(test_code)
    print("\nProcessed:")
    print(result)
