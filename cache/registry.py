"""Volatile cache registry - in-memory cache configuration management.

This module maintains a volatile dictionary of cache configurations loaded from
Squid configuration at startup. Caches are not persisted to the database as they
are completely replaced on program initialization.
"""
from typing import Dict, List, Optional, Tuple
from config.config import MyConfig


def load_caches(caches_data: List[Tuple[str, str, int]]) -> None:
    """
    Load cache configurations into the volatile registry.
    
    This completely replaces the current registry with fresh data.
    Called at program startup by fill_caches() after parsing squid.conf.
    
    Args:
        caches_data: List of tuples (name, ip, access_cost)
    """
    config = MyConfig()
    caches_registry = {}
    
    for name, ip, access_cost in caches_data:
        caches_registry[name] = {
            'ip': ip,
            'access_cost': int(access_cost)
        }
    
    config.set_key('caches', caches_registry)


def _ensure_loaded() -> None:
    """
    Ensure the volatile registry is populated. This attempts a best-effort
    load by calling `fill_caches()` from `cache.cache_manager` if the
    registry is currently empty. The import and call are done lazily to
    avoid circular imports at module import time. All errors are swallowed
    so callers degrade gracefully.
    """
    config = MyConfig()
    caches_registry = config.get_key('caches')
    if caches_registry:
        return

    try:
        # Local import to avoid circular import at module load time.
        from cache.cache_manager import fill_caches
        try:
            fill_caches()
        except Exception:
            # If filling caches fails (missing file, permissions, etc.), do nothing
            pass
    except Exception:
        # If cache_manager isn't importable in this environment, ignore.
        pass


def get_all_caches() -> Dict[str, Dict[str, any]]:
    """
    Get all cached configurations.
    
    Returns:
        Copy of the entire registry
    """
    _ensure_loaded()
    config = MyConfig()
    caches_registry = config.get_key('caches') or {}
    return caches_registry.copy()


def set_miss_cost(cost: int) -> None:
    """Set the miss penalty cost used when computing total costs.

    Args:
        cost: Numeric penalty cost for misses
    """
    config = MyConfig()
    try:
        config.set_key('miss_penalty', int(cost))
    except (TypeError, ValueError):
        # Keep previous value on invalid input
        pass

def set_salsa2_v(salsa_v: int) -> None:
    """Set salsa2 version.

    Args:
        cost: Numeric penalty cost for misses
    """
    config = MyConfig()
    try:
        config.set_key('salsa2_v', int(salsa_v))
    except (TypeError, ValueError):
        # Keep previous value on invalid input
        pass
