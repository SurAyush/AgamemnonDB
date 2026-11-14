from storage.storage_manager import StorageManager
from engine.write_engine import WriteEngine
# from engine.query_engine import QueryEngine
from background.flusher import BackgroundFlusher


class VectorDB:
    def __init__(
        self,
        dimension: int,
        data_dir: str = "data/segments",
        flush_threshold: int = 1000,
        flush_interval: float = 60.0,
    ):
        self.storage = StorageManager(
            dimension=dimension,
            data_dir=data_dir,
            flush_threshold=flush_threshold,
        )

        self.flusher = BackgroundFlusher(
            storage_manager=self.storage,
            flush_interval=flush_interval,
        )

        self.write_engine = WriteEngine(
            storage_manager=self.storage,
            on_flush_needed=self.flusher.notify_size,
        )

        # self.query_engine = QueryEngine(
        #     storage_manager=self.storage,
        # )


    def start(self):
        self.flusher.start()

    def insert(self, vector, metadata=None):
        return self.write_engine.insert(vector, metadata)

    def delete(self, vector_id: int):
        return self.write_engine.delete(vector_id)

    # def search(self, query, k: int = 5):
    #     return self.query_engine.search(query, k)

    def stop(self):
        self.flusher.stop()