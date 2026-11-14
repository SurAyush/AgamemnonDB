import hnswlib
import numpy as np

from pathlib import Path
from storage.memtable import Memtable


class SSTable:

    def __init__(
        self,
        dimension: int,
        path: str,
        M: int = 16,                  # more will make the index more accurate but slower to build and more memory intensive
        ef_construction: int = 400,   # more will make the index more accurate but slower to build
        ef_search: int = 50           # more will make the search more accurate but slower
    ):
        self.dimension = dimension
        self.path = Path(path)

        self.M = M
        self.ef_construction = ef_construction
        self.ef_search = ef_search

        self.index = None
        self.built = False

    def build(self, memtable: Memtable):

        if self.built:
            raise RuntimeError("SSTable has already been built")

        # Step 1: Take a snapshot of the Memtable.
        ids, vectors = memtable.snapshot()

        if ids is None:
            raise ValueError("Cannot build an empty SSTable")

        if vectors.shape[1] != self.dimension:
            raise ValueError("Vector dimension mismatch")

        # Step 2: Initialize HNSW index.
        index = hnswlib.Index(
            space="cosine",
            dim=self.dimension
        )

        index.init_index(
            max_elements=len(ids),
            M=self.M,
            ef_construction=self.ef_construction
        )

        # Step 3: Build the index.
        index.add_items(vectors, ids)

        index.set_ef(self.ef_search)

        # Step 4: Persist the index.
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        index.save_index(str(self.path))

        self.index = index
        self.built = True

    def search(self, query: list[float], k: int = 5):

        if not self.built:
            raise RuntimeError("SSTable has not been built")

        if k <= 0:
            raise ValueError("k must be positive")

        query = np.asarray(query, dtype=np.float32)

        if query.ndim != 1 or query.size != self.dimension:
            raise ValueError("Query dimension mismatch")

        if not np.all(np.isfinite(query)):
            raise ValueError("Query contains non-finite values")

        norm = np.linalg.norm(query)

        if norm == 0:
            raise ValueError("Zero query vector is not supported")

        query = query / norm

        count = min(k, self.index.get_current_count())

        if count == 0:
            return []

        labels, distances = self.index.knn_query(
            query.reshape(1, -1),
            k=count
        )

        results = []

        for vector_id, distance in zip(labels[0], distances[0]):
            results.append({
                "id": int(vector_id),
                "score": float(1.0 - distance)
            })

        return results
