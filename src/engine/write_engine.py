class WriteEngine:
    def __init__(self, storage_manager, on_flush_needed):
        self.storage_manager = storage_manager
        self.on_flush_needed = on_flush_needed
        self._next_id = 0    # will be replaced with a more robust ID generation mechanism in the future

    def insert(self, vector, metadata=None):
        vector_id = self._generate_id()

        should_flush = self.storage_manager.insert(
            vector_id=vector_id,
            vector=vector,
        )

        if should_flush:
            self.on_flush_needed()

        return vector_id

    def delete(self, vector_id: int):
        return self.storage_manager.delete(vector_id)

    def _generate_id(self):
        vector_id = self._next_id
        self._next_id += 1
        return vector_id