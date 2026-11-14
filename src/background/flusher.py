import logging
import queue
import threading

from storage.storage_manager import StorageManager


logger = logging.getLogger(__name__)


class BackgroundFlusher:

    def __init__(
        self,
        storage_manager: StorageManager,
        flush_interval: float = 60.0
    ):
        self.storage_manager = storage_manager
        self.flush_interval = flush_interval

        # A bounded queue prevents duplicate flush events
        # from accumulating when inserts arrive rapidly.
        self.events = queue.Queue(maxsize=1)

        self.stop_event = threading.Event()
        self.thread = None

    def start(self):

        if self.thread is not None and self.thread.is_alive():
            return

        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self._run,
            name="vectordb-flusher",
            daemon=True
        )

        self.thread.start()

        logger.info("Background flusher started")

    def notify_size(self):

        try:
            self.events.put_nowait("size")
        except queue.Full:
            # A flush event is already pending.
            pass

    def _run(self):

        while not self.stop_event.is_set():

            try:
                trigger = self.events.get(
                    timeout=self.flush_interval
                )

            except queue.Empty:
                trigger = "time"

            if self.stop_event.is_set():
                break

            try:
                flushed = self.storage_manager.flush_due(
                    trigger=trigger,
                    flush_interval=self.flush_interval
                )

                if flushed:
                    logger.info(
                        "Memtable successfully flushed"
                    )

            except Exception:
                # Failed frozen Memtables remain searchable.
                # They will be retried on the next event or timer.
                logger.exception("Memtable flush failed")

            finally:
                if trigger == "size":
                    self.events.task_done()

        logger.info("Background flusher stopped")

    def stop(self):

        self.stop_event.set()

        # Wake up the worker if it is waiting on the queue.
        try:
            self.events.put_nowait("stop")
        except queue.Full:
            pass

        if self.thread is not None:
            self.thread.join()

        self.thread = None
