import threading
from pathlib import Path

from storage.memtable import Memtable
from storage.sstable import SSTable


class StorageManager:

    def __init__(
        self,
        dimension: int,
        data_dir: str = "data/segments",
        flush_threshold: int = 1000
    ):
        self.dimension = dimension
        self.data_dir = Path(data_dir)
        self.flush_threshold = flush_threshold

        self._state_lock = threading.RLock()

        self.active_memtable = Memtable()

        # generation -> frozen Memtable
        self.frozen_memtables = {}

        self.sstables = []

        self._next_generation = 0

    # -------------------------
    # WRITE
    # -------------------------

    def insert(self, vector_id, vector, metadata=None):

        with self._state_lock:
            self.active_memtable.insert(
                vector_id,
                vector,
                metadata
            )

            return len(self.active_memtable) >= self.flush_threshold

    # -------------------------
    # READ
    # -------------------------

    def search(self, query, k=5):

        # Capture a consistent set of references.
        with self._state_lock:
            memtables = [
                self.active_memtable,
                *self.frozen_memtables.values()
            ]

            sstables = list(self.sstables)

        # Search without holding the state lock.
        results = []

        for memtable in memtables:
            results.extend(memtable.search(query, k))

        for sstable in sstables:
            results.extend(sstable.search(query, k))

        # Global top-k.
        results.sort(
            key=lambda result: result["score"],
            reverse=True
        )

        return results[:k]

    # -------------------------
    # MEMTABLE ROTATION
    # -------------------------

    def rotate_memtable(self):

        with self._state_lock:

            if len(self.active_memtable) == 0:
                return None

            generation = self._next_generation
            self._next_generation += 1

            frozen = self.active_memtable

            self.frozen_memtables[generation] = frozen

            # New writes go to this Memtable.
            self.active_memtable = Memtable()

            return generation, frozen

    # -------------------------
    # FLUSH
    # -------------------------

    def flush_due(self, trigger, flush_interval):

        with self._state_lock:

            # Retry a previously failed flush first.
            if self.frozen_memtables:
                generation = min(self.frozen_memtables)
                frozen = self.frozen_memtables[generation]

            else:
                active = self.active_memtable
                count = len(active)

                if count == 0:
                    return False

                if trigger == "size":
                    if count < self.flush_threshold:
                        return False

                elif trigger == "time":
                    age = active.age_since_first_write()

                    if age is None or age < flush_interval:
                        return False
                    
                else:
                    return False

                rotated = self.rotate_memtable()

                if rotated is None:
                    return False

                generation, frozen = rotated

        # IMPORTANT:
        # No state lock is held during HNSW construction.

        segment_path = (
            self.data_dir / f"segment_{generation:06d}.bin"
        )

        sstable = SSTable(
            dimension=self.dimension,
            path=str(segment_path)
        )

        # If this fails, frozen remains registered and searchable.
        sstable.build(frozen)

        # Atomically switch the read registry.
        with self._state_lock:

            self.sstables.append(sstable)

            del self.frozen_memtables[generation]

        # Do not clear frozen manually.
        # Existing readers may still hold references to it.

        return True
