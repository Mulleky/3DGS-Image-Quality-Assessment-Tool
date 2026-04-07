"""Duplicate and near-duplicate heuristics for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from splatscout.types import DuplicateCluster, ImageRecord


@dataclass(slots=True)
class _HashRecord:
    path: str
    bits: int


def compute_average_hash(path: Path, hash_size: int = 8) -> int:
    with Image.open(path) as image:
        grayscale = image.convert("L").resize((hash_size, hash_size))
        pixels = np.asarray(grayscale, dtype=np.float32)
    mean_value = float(pixels.mean())
    bits = pixels > mean_value
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bool(bit))
    return value


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def detect_duplicate_clusters(records: list[ImageRecord], distance_threshold: int) -> list[DuplicateCluster]:
    hash_records: list[_HashRecord] = []
    for record in records:
        if not record.readable or not record.source_exists:
            continue
        path = Path(record.path)
        try:
            hash_value = compute_average_hash(path)
        except OSError:
            continue
        record.perceptual_hash = f"{hash_value:016x}"
        hash_records.append(_HashRecord(path=record.path, bits=hash_value))

    if len(hash_records) < 2:
        return []

    parent = {record.path: record.path for record in hash_records}

    def find(path: str) -> str:
        while parent[path] != path:
            parent[path] = parent[parent[path]]
            path = parent[path]
        return path

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    distances: dict[tuple[str, str], int] = {}
    for index, left in enumerate(hash_records):
        for right in hash_records[index + 1 :]:
            distance = hamming_distance(left.bits, right.bits)
            distances[(left.path, right.path)] = distance
            if distance <= distance_threshold:
                union(left.path, right.path)

    groups: dict[str, list[str]] = {}
    for record in hash_records:
        groups.setdefault(find(record.path), []).append(record.path)

    clusters: list[DuplicateCluster] = []
    for root, members in groups.items():
        if len(members) < 2:
            continue
        pair_distances: list[int] = []
        for index, left in enumerate(members):
            for right in members[index + 1 :]:
                pair_distances.append(
                    distances.get((left, right), distances.get((right, left), 0))
                )
        average_distance = sum(pair_distances) / len(pair_distances) if pair_distances else 0.0
        clusters.append(
            DuplicateCluster(
                representative=root,
                members=sorted(members),
                average_distance=average_distance,
                exact=all(distance == 0 for distance in pair_distances),
            )
        )
    return sorted(clusters, key=lambda cluster: (len(cluster.members) * -1, cluster.representative))
