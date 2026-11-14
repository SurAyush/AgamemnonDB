import time
import threading
from typing import Any

import numpy as np


class Memtable:

    def __init__(self):
        self.ids: list[int] = []
        self.vectors: list[np.ndarray] = []
        self.metadata: dict[int, dict[str, Any]] = {}   # will replace using a database engine in the future - RocksDB

        self.dimension: int | None = None
        
        self.first_write_at = None

        self._lock = threading.RLock()

    def snapshot(self):
        with self._lock:
            if not self.vectors:
                return None, None

            ids = np.array(self.ids, dtype=np.int64, copy=True)
            vectors = np.stack(self.vectors).copy()

            return ids, vectors

    def insert(
        self,
        vector_id: int,
        vector: list[float],
        metadata: dict | None = None
    ) -> None:

        with self._lock:

            if vector_id in self.ids:
                raise ValueError(f"ID {vector_id} already exists")

            vector = np.asarray(vector, dtype=np.float32)

            if vector.ndim != 1 or vector.size == 0:
                raise ValueError("Vector must be a non-empty 1D array")

            if not np.all(np.isfinite(vector)):
                raise ValueError("Vector contains non-finite values")

            if self.dimension is None:
                self.dimension = vector.size

            if self.first_write_at is None:
                self.first_write_at = time.monotonic()

            elif vector.size != self.dimension:
                raise ValueError(
                    f"Expected dimension {self.dimension}, "
                    f"got {vector.size}"
                )

            norm = np.linalg.norm(vector)

            if norm == 0:
                raise ValueError("Zero vectors are not supported")

            # Normalize once during insertion for cosine similarity.
            normalized_vector = vector / norm

            self.ids.append(vector_id)
            self.vectors.append(normalized_vector)
            self.metadata[vector_id] = metadata or {}

    def delete(self, vector_id: int) -> bool:

        with self._lock:

            if vector_id not in self.ids:
                return False

            index = self.ids.index(vector_id)

            self.ids.pop(index)
            self.vectors.pop(index)
            del self.metadata[vector_id]

            return True

    def search(
        self,
        query: list[float],
        k: int = 5
    ) -> list[dict]:

        if k <= 0:
            raise ValueError("k must be greater than zero")

        with self._lock:

            if not self.vectors:
                return []

            query = np.asarray(query, dtype=np.float32)

            if query.ndim != 1 or query.size != self.dimension:
                raise ValueError(
                    f"Expected query dimension {self.dimension}"
                )

            if not np.all(np.isfinite(query)):
                raise ValueError("Query contains non-finite values")

            norm = np.linalg.norm(query)

            if norm == 0:
                raise ValueError("Zero query vector is not supported")

            query = query / norm

            # Convert list of vectors into an N x D matrix.
            matrix = np.stack(self.vectors)

            # Vectorized cosine similarity: N x D @ D -> N
            scores = matrix @ query

            k = min(k, len(self.vectors))

            # Get indices of the top-k scores.
            top_indices = np.argpartition(
                scores, len(scores) - k
            )[-k:]

            # Sort only the selected top-k candidates.
            top_indices = top_indices[
                np.argsort(scores[top_indices])[::-1]
            ]

            results = []

            for index in top_indices:
                vector_id = self.ids[index]

                results.append({
                    "id": vector_id,
                    "score": float(scores[index]),
                    "metadata": self.metadata[vector_id].copy()
                })

            return results

    def __len__(self) -> int:
        with self._lock:
            return len(self.ids)

    def age_since_first_write(self):
        
        with self._lock:
            if self.first_write_at is None:
                return None

            return time.monotonic() - self.first_write_at
