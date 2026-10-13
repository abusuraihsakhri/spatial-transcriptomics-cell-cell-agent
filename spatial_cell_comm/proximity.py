"""Descriptive, radius-based cell-type proximity analysis.

Each row represents a cell or spot with an ID, a categorical cell type, and two
coordinates in the same Euclidean coordinate system. Proximity is NOT evidence
of ligand-receptor signaling or molecular interaction.
"""
from collections import defaultdict
from math import floor, hypot, isfinite
from typing import Any, Iterable, Mapping


def analyze_proximity(
    rows: Iterable[Mapping[str, Any]],
    radius: float,
    max_cells: int = 5000,
) -> dict[str, Any]:
    """Count unordered cell-type pairs within an inclusive spatial radius.

    A spatial hash keeps the expected cost near O(n + number_of_local_pairs).
    Each unordered cell pair is counted exactly once, including same-type pairs.
    No coordinate normalization or inferential statistics are performed.
    """
    radius = float(radius)
    if not isfinite(radius) or radius <= 0:
        raise ValueError("radius must be a finite positive number")

    grid: dict[tuple[int, int], list[tuple[float, float, str]]] = defaultdict(list)
    counts: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0, 0.0])
    seen_ids: set[str] = set()
    types: set[str] = set()
    n_cells = 0
    n_pairs = 0

    for index, row in enumerate(rows, 1):
        if n_cells >= max_cells:
            raise ValueError(f"Input exceeds the {max_cells} cell/spot limit")
        try:
            cell_id = str(row["cell_id"]).strip()
            cell_type = str(row["cell_type"]).strip()
            x = float(row["x"])
            y = float(row["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Row {index}: expected cell_id, cell_type, x and y") from exc
        if not cell_id or not cell_type:
            raise ValueError(f"Row {index}: cell_id and cell_type must not be empty")
        if cell_id in seen_ids:
            raise ValueError(f"Row {index}: duplicate cell_id {cell_id!r}")
        if not isfinite(x) or not isfinite(y):
            raise ValueError(f"Row {index}: coordinates must be finite")

        seen_ids.add(cell_id)
        types.add(cell_type)
        bucket = (floor(x / radius), floor(y / radius))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for px, py, previous_type in grid.get((bucket[0] + dx, bucket[1] + dy), ()):
                    distance = hypot(x - px, y - py)
                    if distance <= radius:
                        pair = tuple(sorted((cell_type, previous_type)))
                        counts[pair][0] += 1
                        counts[pair][1] += distance
                        n_pairs += 1
        grid[bucket].append((x, y, cell_type))
        n_cells += 1

    if n_cells == 0:
        raise ValueError("Input has no cell/spot records")

    pair_counts = [
        {
            "type_a": a,
            "type_b": b,
            "contacts": int(values[0]),
            "mean_distance": values[1] / values[0],
        }
        for (a, b), values in sorted(counts.items())
    ]
    return {
        "n_cells": n_cells,
        "n_cell_types": len(types),
        "n_pairs": n_pairs,
        "radius": radius,
        "pair_counts": pair_counts,
        "method": "Euclidean distance <= radius; unordered pairs counted once",
        "interpretation": "Descriptive spatial proximity only; not ligand-receptor interaction or statistical significance",
    }
