"""
AST parser for LumosInterface IDL.

Handles parsing of IDL files using Lark grammar and indentation preprocessing.
"""

from pathlib import Path
from typing import Optional
from lark import Lark, Tree
from lark.exceptions import LarkError

from .grammar_loader import load_grammar
from .preprocessor import IndentationPreprocessor
from ..ast.types import ParseResult, ParseError, FileInfo
from ..config import Config


class ASTParser:
    """Parser for LumosInterface IDL files."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the parser.

        Args:
            config: Configuration object (optional)
        """
        self.config = config or Config.default()
        self.parser = load_grammar()
        self.preprocessor = IndentationPreprocessor()

    def parse_file(self, file_path: str) -> ParseResult:
        """
        Parse a single IDL file.

        Args:
            file_path: Path to .msg file

        Returns:
            ParseResult with parsed AST and any errors
        """
        result = ParseResult()
        path = Path(file_path)

        if not path.exists():
            result.add_error(ParseError(
                file_path=path,
                line=0,
                column=0,
                message=f"File not found: {file_path}",
                error_type="file_not_found"
            ))
            return result

        try:
            # Read file content
            with open(path, 'r') as f:
                content = f.read()

            # Preprocess indentation
            preprocessed = self.preprocessor.process(content)

            # Parse with Lark
            ast = self.parser.parse(preprocessed)

            # Create FileInfo
            file_info = FileInfo(
                path=path,
                namespace=self._derive_namespace(path),
                ast=ast
            )

            # Extract basic information from AST
            self._extract_file_info(file_info, ast)

            result.files[path] = file_info

        except IndentationError as e:
            result.add_error(ParseError(
                file_path=path,
                line=0,
                column=0,
                message=str(e),
                error_type="indentation_error"
            ))

        except LarkError as e:
            # Try to extract line/column info from Lark error
            line = getattr(e, 'line', 0)
            column = getattr(e, 'column', 0)

            result.add_error(ParseError(
                file_path=path,
                line=line,
                column=column,
                message=str(e),
                error_type="syntax_error"
            ))

        except Exception as e:
            result.add_error(ParseError(
                file_path=path,
                line=0,
                column=0,
                message=f"Unexpected error: {e}",
                error_type="internal_error"
            ))

        return result

    def parse_string(self, content: str, file_path: str = "<string>") -> ParseResult:
        """
        Parse IDL content from a string.

        Args:
            content: IDL source code
            file_path: Virtual file path for error reporting

        Returns:
            ParseResult with parsed AST and any errors
        """
        result = ParseResult()
        path = Path(file_path)

        try:
            # Preprocess indentation
            preprocessed = self.preprocessor.process(content)

            # Parse with Lark
            ast = self.parser.parse(preprocessed)

            # Create FileInfo
            file_info = FileInfo(
                path=path,
                namespace=self._derive_namespace(path),
                ast=ast
            )

            # Extract basic information from AST
            self._extract_file_info(file_info, ast)

            result.files[path] = file_info

        except IndentationError as e:
            result.add_error(ParseError(
                file_path=path,
                line=0,
                column=0,
                message=str(e),
                error_type="indentation_error"
            ))

        except LarkError as e:
            line = getattr(e, 'line', 0)
            column = getattr(e, 'column', 0)

            result.add_error(ParseError(
                file_path=path,
                line=line,
                column=column,
                message=str(e),
                error_type="syntax_error"
            ))

        except Exception as e:
            result.add_error(ParseError(
                file_path=path,
                line=0,
                column=0,
                message=f"Unexpected error: {e}",
                error_type="internal_error"
            ))

        return result

    def _derive_namespace(self, file_path: Path) -> str:
        """
        Derive namespace from file path.

        Examples:
            common/geometry.msg -> common::geometry
            interfaces/robot_state.msg -> interfaces::robot_state

        Args:
            file_path: Path to .msg file

        Returns:
            Namespace string
        """
        # Remove .msg extension
        path_without_ext = file_path.with_suffix('')

        # Convert path separators to ::
        parts = path_without_ext.parts

        # If path is absolute, skip root and use relative parts
        # Otherwise use all parts
        if file_path.is_absolute():
            # Find where the actual package structure starts
            # For now, just use the filename without directory
            # This can be improved with search_paths configuration
            return parts[-1]
        else:
            return "::".join(parts)

    def _extract_file_info(self, file_info: FileInfo, ast: Tree):
        """
        Extract imports, type definitions, etc. from AST.

        This is a basic extraction - full semantic analysis happens in validation phase.

        Args:
            file_info: FileInfo to populate
            ast: Parsed AST
        """
        # Extract imports
        for import_node in ast.find_data("import_stmt"):
            # import_node.children[0] is the import_path
            import_path_node = import_node.children[0]
            # import_path is a tree with path_segment children
            path_segments = []
            for segment in import_path_node.children:
                if hasattr(segment, 'value'):
                    path_segments.append(segment.value)
                elif hasattr(segment, 'children'):
                    # Handle dotted segments like geo.types
                    for part in segment.children:
                        if hasattr(part, 'value'):
                            path_segments.append(part.value)

            import_path = "/".join(path_segments)
            file_info.imports.append(import_path)

        # Extract using namespace statements
        for using_ns_node in ast.find_data("using_namespace_stmt"):
            # Extract namespace from qualified_namespace
            namespace = self._extract_qualified_name(using_ns_node.children[0])
            file_info.using_namespaces.append(namespace)

        # Extract namespace aliases
        for ns_alias_node in ast.find_data("namespace_alias_stmt"):
            # namespace alias = target
            alias_name = ns_alias_node.children[0].value
            target_namespace = self._extract_qualified_name(ns_alias_node.children[1])
            file_info.namespace_aliases[alias_name] = target_namespace

        # Note: Type definitions, constants, and aliases will be extracted
        # in the validation phase where we have full context

    def _extract_qualified_name(self, node: Tree) -> str:
        """
        Extract a qualified namespace name from AST node.

        Args:
            node: qualified_namespace node

        Returns:
            Namespace string like "common::geometry"
        """
        parts = []
        for child in node.children:
            if hasattr(child, 'value'):
                parts.append(child.value)
        return "::".join(parts)
