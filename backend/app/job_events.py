from __future__ import annotations

import queue
import threading


class JobEventHub:
    """Thread-safe in-memory event hub for short-lived job updates."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[queue.Queue[None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, job_id: str) -> queue.Queue[None]:
        event_queue: queue.Queue[None] = queue.Queue(maxsize=20)
        with self._lock:
            self._subscribers.setdefault(job_id, set()).add(event_queue)
        return event_queue

    def unsubscribe(self, job_id: str, event_queue: queue.Queue[None]) -> None:
        with self._lock:
            subscribers = self._subscribers.get(job_id)
            if subscribers is None:
                return
            subscribers.discard(event_queue)
            if not subscribers:
                self._subscribers.pop(job_id, None)

    def publish(self, job_id: str) -> None:
        with self._lock:
            subscribers = tuple(self._subscribers.get(job_id, ()))

        for event_queue in subscribers:
            try:
                event_queue.put_nowait(None)
            except queue.Full:
                # The next notification still represents the latest database state.
                pass


job_events = JobEventHub()
