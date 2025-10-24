"""
Collection validator for LumosInterface IDL.

Validates array, matrix, and tensor size constraints.
"""

from typing import List
from lark import Tree
from ..ast.types import TypeInfo, FieldInfo, ValidationError
from ..config import Config


class CollectionValidator:
    """Validates collection type constraints."""

    def __init__(self, config: Config):
        """
        Initialize collection validator.

        Args:
            config: Configuration object
        """
        self.config = config

    def validate_collections(self, type_info: TypeInfo) -> List[ValidationError]:
        """
        Validate all collection fields in a type.

        Args:
            type_info: TypeInfo to validate

        Returns:
            List of validation errors
        """
        errors = []

        for field in type_info.fields:
            # Check if field type indicates a collection
            if field.type_name in ('array', 'matrix', 'tensor'):
                # Need to extract collection info from AST node
                # For now, skip detailed validation since we need AST access
                pass

        return errors

    def validate_collection_field(self, field_node: Tree, file_path, line_number: int) -> List[ValidationError]:
        """
        Validate a collection field from its AST node.

        Args:
            field_node: AST node for the field
            file_path: Path to file containing the field
            line_number: Line number of the field

        Returns:
            List of validation errors
        """
        errors = []

        # Find collection_type node
        for child in field_node.children:
            if hasattr(child, 'data'):
                if child.data == 'collection_type':
                    errors.extend(self._validate_collection_type(child, file_path, line_number))
                elif child.data in ('array_type', 'matrix_type', 'tensor_type'):
                    if child.data == 'array_type':
                        errors.extend(self._validate_array(child, file_path, line_number))
                    elif child.data == 'matrix_type':
                        errors.extend(self._validate_matrix(child, file_path, line_number))
                    elif child.data == 'tensor_type':
                        errors.extend(self._validate_tensor(child, file_path, line_number))

        return errors

    def _validate_collection_type(self, coll_node: Tree, file_path, line_number: int) -> List[ValidationError]:
        """Validate collection_type node (dispatches to specific validators)."""
        errors = []

        for child in coll_node.children:
            if hasattr(child, 'data'):
                if child.data == 'array_type':
                    errors.extend(self._validate_array(child, file_path, line_number))
                elif child.data == 'matrix_type':
                    errors.extend(self._validate_matrix(child, file_path, line_number))
                elif child.data == 'tensor_type':
                    errors.extend(self._validate_tensor(child, file_path, line_number))

        return errors

    def _validate_array(self, array_node: Tree, file_path, line_number: int) -> List[ValidationError]:
        """
        Validate array type.

        Rules:
        - Fixed size must be > 0
        - Max size must be > 0
        """
        errors = []

        # Extract size specs if present (can be fixed_size, max_size, or dynamic_size)
        for child in array_node.children:
            if hasattr(child, 'data'):
                if child.data in ('fixed_size', 'max_size', 'dynamic_size'):
                    errors.extend(self._validate_size_node(child, file_path, line_number, "array"))

        return errors

    def _validate_matrix(self, matrix_node: Tree, file_path, line_number: int) -> List[ValidationError]:
        """
        Validate matrix type.

        Rules:
        - Must have exactly 2 dimensions
        - Each dimension must be > 0 (if fixed)
        """
        errors = []

        # Count size specs (fixed_size, max_size, or dynamic_size)
        size_nodes = [child for child in matrix_node.children
                      if hasattr(child, 'data') and child.data in ('fixed_size', 'max_size', 'dynamic_size')]

        if len(size_nodes) != 2:
            errors.append(ValidationError(
                file_path=file_path,
                line=line_number,
                column=0,
                message=f"Matrix must have exactly 2 dimensions, found {len(size_nodes)}",
                error_type="invalid_matrix_dimensions",
                severity="error"
            ))
        else:
            # Validate each dimension
            for size_node in size_nodes:
                errors.extend(self._validate_size_node(size_node, file_path, line_number, "matrix"))

        return errors

    def _validate_tensor(self, tensor_node: Tree, file_path, line_number: int) -> List[ValidationError]:
        """
        Validate tensor type.

        Rules:
        - Must have at least 1 dimension
        - Each dimension must be > 0 (if fixed)
        """
        errors = []

        # Count size specs (fixed_size, max_size, or dynamic_size)
        size_nodes = [child for child in tensor_node.children
                      if hasattr(child, 'data') and child.data in ('fixed_size', 'max_size', 'dynamic_size')]

        if len(size_nodes) < 1:
            errors.append(ValidationError(
                file_path=file_path,
                line=line_number,
                column=0,
                message="Tensor must have at least 1 dimension",
                error_type="invalid_tensor_dimensions",
                severity="error"
            ))
        else:
            # Validate each dimension
            for size_node in size_nodes:
                errors.extend(self._validate_size_node(size_node, file_path, line_number, "tensor"))

        return errors

    def _validate_size_node(self, size_node: Tree, file_path, line_number: int, collection_type: str) -> List[ValidationError]:
        """
        Validate a size node (fixed_size, max_size, or dynamic_size).

        Rules:
        - fixed_size: must be > 0
        - max_size: must be > 0
        - dynamic_size (?): always valid
        """
        errors = []

        if size_node.data == 'fixed_size':
            # Extract the size value (it's a direct child token)
            if len(size_node.children) > 0:
                size_value = int(size_node.children[0].value)
                if size_value <= 0:
                    errors.append(ValidationError(
                        file_path=file_path,
                        line=line_number,
                        column=0,
                        message=f"Fixed size must be > 0 in {collection_type}, got {size_value}",
                        error_type="invalid_collection_size",
                        severity="error"
                    ))
        elif size_node.data == 'max_size':
            # Extract the max size value
            if len(size_node.children) > 0:
                max_value = int(size_node.children[0].value)
                if max_value <= 0:
                    errors.append(ValidationError(
                        file_path=file_path,
                        line=line_number,
                        column=0,
                        message=f"Max size must be > 0 in {collection_type}, got max={max_value}",
                        error_type="invalid_collection_size",
                        severity="error"
                    ))
        # dynamic_size (?) is always valid

        return errors
