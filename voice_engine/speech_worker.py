"""
Speech Worker

Background text-to-speech worker for the AI Fitness Tracker.

Responsibilities:
    - Read voice events from SpeechQueue.
    - Speak events using pyttsx3.
    - Run speech in a background thread.
    - Never block the workout / camera loop.
    - Start and stop safely.
    - Prevent crashes from invalid events.

Architecture:

    Workout Engine
          |
          v
    Voice Events
          |
          v
    Speech Queue
          |
          v
    Speech Worker  ---> pyttsx3
                         |
                         v
                       Speaker
"""

import threading
import time

import pyttsx3


class SpeechWorker:
    """
    Background worker responsible for speaking queued events.
    """

    def __init__(
        self,
        speech_queue,
        rate=175,
        volume=1.0,
        idle_sleep=0.02,
    ):
        """
        Parameters
        ----------
        speech_queue:
            SpeechQueue instance.

        rate:
            Speech speed passed to pyttsx3.

        volume:
            Speech volume between 0.0 and 1.0.

        idle_sleep:
            Small sleep used when the queue is empty.
            Lower values improve responsiveness.
        """

        if speech_queue is None:
            raise ValueError(
                "speech_queue cannot be None"
            )

        if rate <= 0:
            raise ValueError(
                "rate must be greater than 0"
            )

        if not 0.0 <= volume <= 1.0:
            raise ValueError(
                "volume must be between 0.0 and 1.0"
            )

        if idle_sleep <= 0:
            raise ValueError(
                "idle_sleep must be greater than 0"
            )

        self.queue = speech_queue

        self.rate = rate
        self.volume = volume
        self.idle_sleep = idle_sleep

        self._thread = None
        self._stop_event = threading.Event()
        self._running = False

        self._engine = None

        self._lock = threading.Lock()

    # ==========================================================
    # START
    # ==========================================================

    def start(self):
        """
        Start the speech worker.

        Returns
        -------
        bool
            True if the worker was started.
            False if already running.
        """

        with self._lock:

            if self._running:
                return False

            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._worker_loop,
                name="SpeechWorker",
                daemon=True,
            )

            self._running = True

            self._thread.start()

            return True

    # ==========================================================
    # WORKER LOOP
    # ==========================================================

    def _worker_loop(self):
        """
        Background speech processing loop.
        """

        try:

            # --------------------------------------------------
            # Create pyttsx3 inside the worker thread.
            # --------------------------------------------------

            self._engine = pyttsx3.init()

            self._engine.setProperty(
                "rate",
                self.rate,
            )

            self._engine.setProperty(
                "volume",
                self.volume,
            )

            # --------------------------------------------------
            # Main loop
            # --------------------------------------------------

            while not self._stop_event.is_set():

                event = self.queue.get()

                # ------------------------------------------------
                # Nothing waiting.
                # ------------------------------------------------

                if event is None:
                    time.sleep(self.idle_sleep)
                    continue

                # ------------------------------------------------
                # Extract message safely.
                # ------------------------------------------------

                message = self._extract_message(event)

                if not message:
                    continue

                # ------------------------------------------------
                # Speak event.
                # ------------------------------------------------

                self._speak(message)

        except Exception as error:

            # The worker must never crash the workout system.
            print(
                f"Speech worker error: {error}"
            )

        finally:

            # --------------------------------------------------
            # Stop speech engine safely.
            # --------------------------------------------------

            try:

                if self._engine is not None:
                    self._engine.stop()

            except Exception:
                pass

            self._engine = None

            with self._lock:
                self._running = False

    # ==========================================================
    # EXTRACT MESSAGE
    # ==========================================================

    @staticmethod
    def _extract_message(event):
        """
        Extract the spoken message from an event.

        Supports dictionary-based voice events.
        """

        if event is None:
            return None

        # ------------------------------------------------------
        # Dictionary event
        # ------------------------------------------------------

        if isinstance(event, dict):

            message = event.get("message")

            if message is None:
                return None

            message = str(message).strip()

            if not message:
                return None

            return message

        # ------------------------------------------------------
        # Object with message attribute
        # ------------------------------------------------------

        if hasattr(event, "message"):

            message = getattr(
                event,
                "message",
                None,
            )

            if message is None:
                return None

            message = str(message).strip()

            if not message:
                return None

            return message

        # ------------------------------------------------------
        # Unsupported event
        # ------------------------------------------------------

        return None

    # ==========================================================
    # SPEAK
    # ==========================================================

    def _speak(self, message):
        """
        Speak a single message.
        """

        if not message:
            return

        if self._engine is None:
            return

        try:

            self._engine.say(message)

            self._engine.runAndWait()

        except Exception as error:

            print(
                f"Speech error: {error}"
            )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self, timeout=2.0):
        """
        Stop the speech worker.

        Parameters
        ----------
        timeout:
            Maximum time to wait for the worker thread.

        Returns
        -------
        bool
            True if stopped successfully.
        """

        self._stop_event.set()

        thread = self._thread

        if thread is not None:

            thread.join(
                timeout=timeout
            )

        with self._lock:

            self._running = False
            self._thread = None

        return True

    # ==========================================================
    # IS RUNNING
    # ==========================================================

    def is_running(self):
        """
        Return whether the worker is currently running.
        """

        with self._lock:
            return self._running

    # ==========================================================
    # QUEUE STATUS
    # ==========================================================

    def pending_events(self):
        """
        Return the number of events waiting to be spoken.
        """

        return self.queue.size()

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear_queue(self):
        """
        Clear all pending speech events.
        """

        self.queue.clear()

    # ==========================================================
    # WAIT UNTIL EMPTY
    # ==========================================================

    def wait_until_empty(self, timeout=10.0):
        """
        Wait until all queued events have been consumed.

        Returns
        -------
        bool
            True if queue became empty.
            False if timeout was reached.
        """

        deadline = time.time() + timeout

        while time.time() < deadline:

            if self.queue.is_empty():
                return True

            time.sleep(
                self.idle_sleep
            )

        return self.queue.is_empty()