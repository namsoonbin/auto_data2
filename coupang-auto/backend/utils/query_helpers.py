# -*- coding: utf-8 -*-
"""
Query helper utilities for safe database operations
"""


def escape_like_pattern(pattern: str) -> str:
    """
    Escape special characters in LIKE pattern to prevent wildcard injection

    Args:
        pattern: User input string to be used in LIKE query

    Returns:
        Escaped string safe for LIKE queries

    Example:
        >>> escape_like_pattern("test%")
        'test\\%'
        >>> escape_like_pattern("test_name")
        'test\\_name'
    """
    if not pattern:
        return pattern

    # Escape backslash first, then wildcards
    return (pattern
            .replace('\\', '\\\\')
            .replace('%', '\\%')
            .replace('_', '\\_'))
