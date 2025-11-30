"""Metrics calculation functions for classification performance analysis."""
from typing import List
from ui.repository import UIRepository


def create_caches_dict(run_id):
    """
    Creates a dictionary from the volatile cache registry
    where each key is a cache name and the value is [TN, FP, FN, TP] initialized to 0.
    This matches the format expected by classification_metrics().
    
    Returns:
        Dictionary with cache names as keys and [TN, FP, FN, TP] as values
    """
    caches = UIRepository.get_caches(run_id)
    caches_dict = {}
    for name, cost in caches:
        caches_dict[name] = [0] * 4  # [TN, FP, FN, TP]
        caches_dict[name].append(cost)

    # Also add 'Sum' row for totals
    caches_dict['Sum'] = [0] * 4
    caches_dict['Sum'].append("-")
    
    return caches_dict


def classification_metrics(data) -> List[List]:
    """
    Calculate classification metrics (accuracy, recall, precision, F1).
    
    Args:
        data: Dictionary with format {name: [TN, FP, FN, TP]}
        
    Returns:
        List of [name, accuracy, recall, precision, f1] rows.
        All metrics are rounded to 3 decimals. Division by zero returns 0.0.
    """
    results = []
    for name, (TN, FP, FN, TP, cost) in data.items():
        # total number of samples
        total = TN + FN + FP + TP

        # Accuracy = (TP + TN) / total
        accuracy = (TP + TN) / total if total > 0 else 0.0

        # Recall = TP / (TP + FN)
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0

        # Precision = TP / (TP + FP)
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0

        # F1 = harmonic mean of precision and recall
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)

        # append row: [name, accuracy, recall, precision, f1, cost]
        results.append([
            name,
            round(accuracy, 3),
            round(recall, 3),
            round(precision, 3),
            round(f1, 3),
            cost
        ])

    return results


def analyze_request_caches(req_id: int, run_id : int = None):
    """
    Analyze cache performance metrics for a single request.
    
    Args:
        req_id: The request ID to analyze
        
    Returns:
        Tuple of (caches_dict with metrics, details dict with fields)
    """
    if run_id:
        caches_dict = create_caches_dict(run_id)
    else:
        caches_dict = None

    details = {
        'indicated': [],
        'accessed': [],
        'resolved': [],
        'hit': False,
        'cost': 0
    }
    
    rows = UIRepository.get_request_cache_details(req_id)

    for (indication, accessed, resolution, name, access_cost) in rows:

        if indication:
            details['indicated'].append(name)
        if accessed:
            details['accessed'].append(name)
            details['cost'] += access_cost or 0  # handle NULL
        if resolution:
            details['resolved'].append(name)

        # true "hit" only if accessed AND resolved
        details['hit'] = details['hit'] or (accessed and resolution)

        if run_id:
            # resType = 0..3 if indication, resolution are 0/1
            # Accuracy metrics check digest accuracy: did our indication match the actual resolution?
            # resType 0: indication=0, resolution=0 → True Negative (TN) index 0
            # resType 1: indication=1, resolution=0 → False Positive (FP) index 1
            # resType 2: indication=0, resolution=1 → False Negative (FN) index 2
            # resType 3: indication=1, resolution=1 → True Positive (TP) index 3
            resType = int(indication) + 2 * int(resolution)
            if not (0 <= resType < 4):
                raise ValueError(f"Unexpected resType {resType} for ({indication=}, {resolution=})")

            if name not in caches_dict:
                raise KeyError(f"Cache name {name!r} not in caches_dict")

            caches_dict[name][resType] += 1
            caches_dict['Sum'][resType] += 1

    return caches_dict, details
