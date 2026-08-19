"""Cache management module for Salsa2 Simulator."""
from .cache_manager import (
    clear_cache, restart_squid, reset_all_caches, is_squid_up, show_caches
)

__all__ = [
    'clear_cache', 'restart_squid', 'reset_all_caches', 'is_squid_up', 'show_caches'
]
