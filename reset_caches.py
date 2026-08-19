#!/usr/bin/env python3
"""
Reset caches - Salsa2 Simulator

Clears all cache data across the squid hierarchy: for each parent cache
(read from squid.conf's cache_peer entries), deletes its on-disk cache
directory and restarts squid so nothing lingers in memory either. This
node forwards to those parents and holds no cache data of its own, so
resetting them clears the whole hierarchy.
"""
import sys

from cache.cache_manager import fill_caches, reset_all_caches
from cache.registry import get_all_caches
from prettytable import PrettyTable


def _confirm(caches: dict) -> bool:
    """Print the target caches and ask the user to confirm before touching them."""
    print("This will delete cache data and restart squid on:")
    for name, info in caches.items():
        print(f"  - {name} ({info['ip']})")

    answer = input("Continue? [y/N]: ").strip().lower()
    return answer == 'y'


def _print_summary(results: list):
    table = PrettyTable()
    table.field_names = ['Name', 'IP', 'Status']

    for name, ip, status in results:
        table.add_row([name, ip, status])

    print(table)


def main():
    fill_caches()

    caches = get_all_caches()
    if not caches:
        print("No parent caches found in squid.conf - nothing to reset.")
        return

    if not _confirm(caches):
        print("Aborted.")
        return

    results = reset_all_caches()

    print()
    _print_summary(results)

    if any(status != 'ok' for _, _, status in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
