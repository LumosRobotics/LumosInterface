"""
Symbol table for LumosInterface IDL validation.

Tracks all defined types, their locations, and visibility.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from ..ast.types import TypeInfo, FileInfo, ConstantInfo, AliasInfo


class SymbolTable:
    """Central registry of all types and their definitions."""

    def __init__(self):
        self.types: Dict[str, TypeInfo] = {}  # Fully qualified name -> TypeInfo
        self.constants: Dict[str, ConstantInfo] = {}  # Fully qualified name -> ConstantInfo
        self.aliases: Dict[str, AliasInfo] = {}  # Fully qualified name -> AliasInfo
        self.files: Dict[Path, FileInfo] = {}  # File path -> FileInfo

    def register_file(self, file_info: FileInfo):
        """
        Register a parsed file.

        Args:
            file_info: FileInfo to register
        """
        self.files[file_info.path] = file_info

    def register_type(self, type_info: TypeInfo):
        """
        Register a type definition.

        Args:
            type_info: TypeInfo to register
        """
        self.types[type_info.qualified_name] = type_info

    def register_constant(self, const_info: ConstantInfo):
        """
        Register a constant definition.

        Args:
            const_info: ConstantInfo to register
        """
        self.constants[const_info.qualified_name] = const_info

    def register_alias(self, alias_info: AliasInfo):
        """
        Register a type alias.

        Args:
            alias_info: AliasInfo to register
        """
        self.aliases[alias_info.qualified_name] = alias_info

    def lookup_type(self, name: str, context: Optional[FileInfo] = None) -> Optional[TypeInfo]:
        """
        Look up a type by name, considering context for resolution.

        Args:
            name: Type name (simple or qualified)
            context: FileInfo for context-aware lookup

        Returns:
            TypeInfo if found, None otherwise
        """
        # Try direct lookup first (for fully qualified names)
        if name in self.types:
            return self.types[name]

        # If no context, can't do context-aware resolution
        if context is None:
            return None

        # Try with file's namespace
        qualified_name = f"{context.namespace}::{name}"
        if qualified_name in self.types:
            return self.types[qualified_name]

        # Try with using namespaces
        for using_ns in context.using_namespaces:
            qualified_name = f"{using_ns}::{name}"
            if qualified_name in self.types:
                return self.types[qualified_name]

        # Try namespace aliases
        for alias, target_ns in context.namespace_aliases.items():
            if name.startswith(f"{alias}::"):
                # Replace alias with target namespace
                rest = name[len(alias) + 2:]  # +2 for "::"
                qualified_name = f"{target_ns}::{rest}"
                if qualified_name in self.types:
                    return self.types[qualified_name]

        return None

    def lookup_constant(self, name: str, context: Optional[FileInfo] = None) -> Optional[ConstantInfo]:
        """
        Look up a constant by name.

        Args:
            name: Constant name (simple or qualified)
            context: FileInfo for context-aware lookup

        Returns:
            ConstantInfo if found, None otherwise
        """
        # Try direct lookup
        if name in self.constants:
            return self.constants[name]

        if context is None:
            return None

        # Try with file's namespace
        qualified_name = f"{context.namespace}::{name}"
        if qualified_name in self.constants:
            return self.constants[qualified_name]

        return None

    def lookup_alias(self, name: str, context: Optional[FileInfo] = None) -> Optional[AliasInfo]:
        """
        Look up a type alias by name.

        Args:
            name: Alias name (simple or qualified)
            context: FileInfo for context-aware lookup

        Returns:
            AliasInfo if found, None otherwise
        """
        # Try direct lookup
        if name in self.aliases:
            return self.aliases[name]

        if context is None:
            return None

        # Try with file's namespace
        qualified_name = f"{context.namespace}::{name}"
        if qualified_name in self.aliases:
            return self.aliases[qualified_name]

        return None

    def resolve_type(self, name: str, using_namespaces: List[str]) -> Optional[str]:
        """
        Resolve a type name to its fully qualified name.

        Args:
            name: Type name to resolve
            using_namespaces: List of namespaces to search

        Returns:
            Fully qualified name if found, None otherwise
        """
        # Already qualified?
        if name in self.types:
            return name

        # Try each using namespace
        for namespace in using_namespaces:
            qualified_name = f"{namespace}::{name}"
            if qualified_name in self.types:
                return qualified_name

        return None

    def get_types_in_namespace(self, namespace: str) -> List[TypeInfo]:
        """
        Get all types defined in a specific namespace.

        Args:
            namespace: Namespace to search

        Returns:
            List of TypeInfo in that namespace
        """
        return [
            type_info
            for type_info in self.types.values()
            if type_info.qualified_name.startswith(f"{namespace}::")
            or type_info.qualified_name == namespace
        ]

    def get_types_in_file(self, file_path: Path) -> List[TypeInfo]:
        """
        Get all types defined in a specific file.

        Args:
            file_path: Path to file

        Returns:
            List of TypeInfo defined in that file
        """
        return [
            type_info
            for type_info in self.types.values()
            if type_info.file_path == file_path
        ]

    def get_all_namespaces(self) -> Set[str]:
        """
        Get all unique namespaces.

        Returns:
            Set of namespace strings
        """
        namespaces = set()
        for type_info in self.types.values():
            # Extract namespace from qualified name
            parts = type_info.qualified_name.split("::")
            if len(parts) > 1:
                namespace = "::".join(parts[:-1])
                namespaces.add(namespace)
        return namespaces

    def type_exists(self, qualified_name: str) -> bool:
        """
        Check if a type exists.

        Args:
            qualified_name: Fully qualified type name

        Returns:
            True if type exists, False otherwise
        """
        return qualified_name in self.types

    def clear(self):
        """Clear all registered symbols."""
        self.types.clear()
        self.constants.clear()
        self.aliases.clear()
        self.files.clear()

    def statistics(self) -> Dict[str, int]:
        """
        Get statistics about registered symbols.

        Returns:
            Dictionary with counts of different symbol types
        """
        return {
            "types": len(self.types),
            "constants": len(self.constants),
            "aliases": len(self.aliases),
            "files": len(self.files),
            "namespaces": len(self.get_all_namespaces()),
        }

    def __repr__(self) -> str:
        stats = self.statistics()
        return (
            f"SymbolTable("
            f"types={stats['types']}, "
            f"constants={stats['constants']}, "
            f"aliases={stats['aliases']}, "
            f"files={stats['files']})"
        )
