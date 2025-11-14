"""HTTP Request execution module for Salsa2 Simulator."""
from .request_executor import execute_req, execute_single_req, get_proxies_for_cache

__all__ = ['execute_req', 'execute_single_req', 'get_proxies_for_cache']
