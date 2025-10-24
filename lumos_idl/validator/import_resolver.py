"""
Import resolver for LumosInterface IDL.

Resolves import statements to actual file paths and detects circular dependencies.
"""

from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from ..ast.types import FileInfo, ValidationError


class ImportResolver:
    """Resolves import paths to file paths."""

    def __init__(self, search_paths: List[Path]):
        """
        Initialize import resolver.

        Args:
            search_paths: Base directories to search for imports
        """
        self.search_paths = search_paths
        self.cache: Dict[str, Optional[Path]] = {}  # Import path -> resolved file path

    def resolve_import(self, import_path: str, context_file: Optional[Path] = None) -> Optional[Path]:
        """
        Convert import path to file path.

        Examples:
            "common/geometry" -> "<search_path>/common/geometry.msg"
            "common/geo.types" -> "<search_path>/common/geo.types.msg"

        Args:
            import_path: Import path from import statement
            context_file: File containing the import (for relative resolution)

        Returns:
            Resolved Path or None if not found
        """
        # Check cache
        if import_path in self.cache:
            return self.cache[import_path]

        # Clean up the import path (remove extra slashes)
        cleaned_path = import_path.replace("///", "/").replace("//", "/")

        # Convert to file path with .msg extension
        file_name = f"{cleaned_path}.msg"

        # Try each search path
        for search_path in self.search_paths:
            candidate = search_path / file_name
            if candidate.exists() and candidate.is_file():
                # Cache and return
                self.cache[import_path] = candidate
                return candidate

        # If context_file is provided, try relative to it
        if context_file is not None:
            relative = context_file.parent / file_name
            if relative.exists() and relative.is_file():
                self.cache[import_path] = relative
                return relative

        # Not found
        self.cache[import_path] = None
        return None

    def resolve_all_imports(self, files: Dict[Path, FileInfo]) -> Dict[Path, List[Tuple[str, Optional[Path]]]]:
        """
        Resolve all imports for all files.

        Args:
            files: Dictionary of FileInfo objects

        Returns:
            Dictionary mapping file paths to list of (import_path, resolved_path) tuples
        """
        results = {}

        for file_path, file_info in files.items():
            imports = []
            for import_path in file_info.imports:
                resolved = self.resolve_import(import_path, file_path)
                imports.append((import_path, resolved))
            results[file_path] = imports

        return results

    def build_dependency_graph(self, files: Dict[Path, FileInfo]) -> Dict[Path, Set[Path]]:
        """
        Build file dependency graph.

        Args:
            files: Dictionary of FileInfo objects

        Returns:
            Adjacency list: file_path -> set of files it depends on
        """
        graph = {}

        for file_path, file_info in files.items():
            dependencies = set()

            for import_path in file_info.imports:
                resolved = self.resolve_import(import_path, file_path)
                if resolved is not None:
                    # Normalize the path
                    dependencies.add(resolved.resolve())

            graph[file_path.resolve()] = dependencies

        return graph

    def detect_cycles(self, graph: Dict[Path, Set[Path]]) -> List[List[Path]]:
        """
        Detect circular dependencies using DFS.

        Args:
            graph: Dependency graph (adjacency list)

        Returns:
            List of cycles, where each cycle is a list of file paths
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path_stack = []

        def dfs(node: Path):
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path_stack.append(node)

            # Visit all dependencies
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        dfs(neighbor)
                    elif neighbor in rec_stack:
                        # Found a cycle
                        cycle_start = path_stack.index(neighbor)
                        cycle = path_stack[cycle_start:] + [neighbor]
                        cycles.append(cycle)

            path_stack.pop()
            rec_stack.remove(node)

        # Run DFS from each unvisited node
        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def validate_imports(self, files: Dict[Path, FileInfo]) -> List[ValidationError]:
        """
        Validate all imports in files.

        Checks:
        1. Import paths resolve to existing files
        2. No circular dependencies

        Args:
            files: Dictionary of FileInfo objects

        Returns:
            List of ValidationErrors
        """
        errors = []

        # Check that all imports resolve
        for file_path, file_info in files.items():
            for import_path in file_info.imports:
                resolved = self.resolve_import(import_path, file_path)

                if resolved is None:
                    errors.append(ValidationError(
                        file_path=file_path,
                        line=0,  # TODO: Get actual line number from AST
                        column=0,
                        message=f"Cannot resolve import '{import_path}'. "
                                f"File not found in search paths: {[str(p) for p in self.search_paths]}",
                        error_type="import_not_found",
                        severity="error"
                    ))

        # Build dependency graph
        graph = self.build_dependency_graph(files)

        # Detect circular dependencies
        cycles = self.detect_cycles(graph)

        for cycle in cycles:
            # Format cycle for error message
            cycle_str = " -> ".join([str(f.name) for f in cycle])

            # Report error on the first file in the cycle
            errors.append(ValidationError(
                file_path=cycle[0],
                line=0,
                column=0,
                message=f"Circular dependency detected: {cycle_str}",
                error_type="circular_dependency",
                severity="error"
            ))

        return errors

    def get_import_order(self, files: Dict[Path, FileInfo]) -> Optional[List[Path]]:
        """
        Get topologically sorted import order.

        Files with no dependencies come first, files that depend on others come after.

        Args:
            files: Dictionary of FileInfo objects

        Returns:
            List of file paths in dependency order, or None if there are cycles
        """
        graph = self.build_dependency_graph(files)

        # Check for cycles first
        cycles = self.detect_cycles(graph)
        if cycles:
            return None

        # Topological sort using Kahn's algorithm
        # Note: Our graph represents "A depends on B" but Kahn's algorithm needs
        # "A must be processed before B", so we treat dependencies as in-degrees

        # Each node's in-degree is the number of files it depends on
        in_degree = {node: len(graph.get(node, set())) for node in graph}

        # Build reverse graph: who depends on me?
        reverse_graph: Dict[Path, Set[Path]] = {node: set() for node in graph}
        for node in graph:
            for dependency in graph[node]:
                if dependency in reverse_graph:
                    reverse_graph[dependency].add(node)

        # Start with nodes that have no dependencies (in-degree 0)
        queue = [node for node in graph if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # When we process a node, reduce in-degree for all files that depend on it
            for dependent in reverse_graph.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If result doesn't contain all nodes, there was a cycle
        if len(result) != len(in_degree):
            return None

        return result

    def get_transitive_dependencies(self, file_path: Path, files: Dict[Path, FileInfo]) -> Set[Path]:
        """
        Get all files that a file depends on (transitively).

        Args:
            file_path: File to get dependencies for
            files: Dictionary of FileInfo objects

        Returns:
            Set of file paths that file_path depends on
        """
        graph = self.build_dependency_graph(files)
        dependencies = set()
        visited = set()

        def dfs(node: Path):
            """DFS to collect all dependencies."""
            if node in visited:
                return
            visited.add(node)

            if node in graph:
                for neighbor in graph[node]:
                    dependencies.add(neighbor)
                    dfs(neighbor)

        dfs(file_path.resolve())
        return dependencies

    def clear_cache(self):
        """Clear the resolution cache."""
        self.cache.clear()
