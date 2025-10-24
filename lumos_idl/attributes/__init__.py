"""
Attribute system for LumosInterface IDL.

Provides extensible attribute validation through schema-based plugins.
"""

from .registry import AttributeRegistry, AttributeSchema, ValidationResult
from .validator import AttributeValidator

__all__ = [
    'AttributeRegistry',
    'AttributeSchema',
    'AttributeValidator',
    'ValidationResult',
]
