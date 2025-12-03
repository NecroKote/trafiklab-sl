"""Helper utilities for SL data.

This module provides the CacheProtocol interface for optional caching support.
"""

from .cache import TTL_STATIC, CacheProtocol

__all__ = [
    "CacheProtocol",
    "TTL_STATIC",
]
