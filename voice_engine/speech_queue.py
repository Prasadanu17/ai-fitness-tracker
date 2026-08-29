"""
Speech Queue

Manages voice events before they are sent to the
text-to-speech worker.

The queue is intentionally independent from:
    - MediaPipe
    - Exercise detection
    - Workout analyzers
    - Screen/UI

This prevents speech processing from blocking the
real-time workout loop.
"""

from collections import deque
from threading import Lock


class SpeechQueue:
    """
    Thread-safe queue for voice events.

    Example:

        queue = SpeechQueue()

        queue.put(event)

        event = queue.get()
    """

    def __init__(self, max_size=20):
        """
        Parameters
        ----------
        max_size : int
            Maximum number of pending speech events.
        """

        if max_size <= 0:
            raise ValueError("max_size must be greater than 0")

        self.max_size = max_size
        self._queue = deque()
        self._lock = Lock()

    # ==========================================================
    # ADD EVENT
    # ==========================================================

    def put(self, event):
        """
        Add a voice event to the queue.

        If the queue is full, the oldest event is removed.

        Returns
        -------
        bool
            True if the event was added.
        """

        if event is None:
            return False

        with self._lock:

            if len(self._queue) >= self.max_size:
                self._queue.popleft()

            self._queue.append(event)

        return True

    # ==========================================================
    # GET EVENT
    # ==========================================================

    def get(self):
        """
        Remove and return the oldest event.

        Returns
        -------
        object or None
            Oldest queued event.
        """

        with self._lock:

            if not self._queue:
                return None

            return self._queue.popleft()

    # ==========================================================
    # PEEK
    # ==========================================================

    def peek(self):
        """
        Return the oldest event without removing it.
        """

        with self._lock:

            if not self._queue:
                return None

            return self._queue[0]

    # ==========================================================
    # SIZE
    # ==========================================================

    def size(self):
        """
        Return the number of pending events.
        """

        with self._lock:
            return len(self._queue)

    # ==========================================================
    # EMPTY
    # ==========================================================

    def is_empty(self):
        """
        Return True if the queue contains no events.
        """

        with self._lock:
            return len(self._queue) == 0

    # ==========================================================
    # FULL
    # ==========================================================

    def is_full(self):
        """
        Return True if the queue has reached max_size.
        """

        with self._lock:
            return len(self._queue) >= self.max_size

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self):
        """
        Remove all pending events.
        """

        with self._lock:
            self._queue.clear()

    # ==========================================================
    # SNAPSHOT
    # ==========================================================

    def get_all(self):
        """
        Return a snapshot of all queued events.

        The queue itself is not modified.
        """

        with self._lock:
            return list(self._queue)

    # ==========================================================
    # LENGTH
    # ==========================================================

    def __len__(self):
        """
        Allow:

            len(queue)
        """

        return self.size()