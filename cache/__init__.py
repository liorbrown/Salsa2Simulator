"""Cache management module for Salsa2 Simulator."""
from .cache_manager import (
    get_miss_cost, clear_cache, is_squid_up, get_cost,
    show_caches
)

__all__ = [
    'get_miss_cost', 'clear_cache', 'is_squid_up',
    'get_cost', 'show_caches'
]
