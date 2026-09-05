import threading
import time


class SpeechWorker:
    """
    Background text-to-speech worker.

    Consumes speech events from SpeechQueue and speaks them
    without blocking the main webcam / workout loop.
    """

    def __init__(
        self,
        speech_queue,
        speech_rate=175,
        speech_volume=1.0,
        debug=False,
    ):
        self.queue = speech_queue
        self.speech_rate = speech_rate
        self.speech_volume = speech_volume
        self.debug = debug

        self._stop_event = threading.Event()
        self._thread = None
        self._engine = None

    def start(self):
        """Start the background speech worker."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="SpeechWorker",
            daemon=True,
        )

        self._thread.start()

        if self.debug:
            print("[VOICE DEBUG] speech worker started")

    def stop(self):
        """
        Stop the worker gracefully.

        Important:
        Already queued speech is allowed to finish before
        the worker exits.
        """
        if self.debug:
            print("[VOICE DEBUG] stopping speech worker...")

        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        self._thread = None

        if self.debug:
            print("[VOICE DEBUG] speech worker stopped")

    def _run(self):
        """Background worker loop."""
        try:
            import pyttsx3

            self._engine = pyttsx3.init()

            self._engine.setProperty(
                "rate",
                self.speech_rate,
            )

            self._engine.setProperty(
                "volume",
                self.speech_volume,
            )

            if self.debug:
                print("[VOICE DEBUG] TTS engine initialized")

        except Exception as exc:
            print(f"[VOICE ERROR] Could not initialize TTS: {exc}")
            self._engine = None

        while True:
            event = self.queue.get()

            if event is None:
                # Queue is empty.
                #
                # If stop was requested and nothing remains
                # to be spoken, exit cleanly.
                if self._stop_event.is_set() and self.queue.size() == 0:
                    break

                time.sleep(0.05)
                continue

            message = self._extract_message(event)

            if not message:
                continue

            if self.debug:
                print(
                    f"[VOICE DEBUG] worker consumed: {message}"
                )

            self._speak(message)

        if self.debug:
            print("[VOICE DEBUG] speech worker loop exited")

    def _extract_message(self, event):
        """Extract speech text from a VoiceEvent/dict/string."""
        if event is None:
            return None

        if isinstance(event, str):
            return event.strip()

        if isinstance(event, dict):
            message = event.get("message")

            if message is None:
                message = event.get("text")

            if message is None:
                message = event.get("speech")

            if message is not None:
                return str(message).strip()

        return None

    def _speak(self, message):
        """Speak one message."""
        if not self._engine:
            if self.debug:
                print(
                    f"[VOICE DEBUG] TTS unavailable: {message}"
                )
            return

        try:
            if self.debug:
                print(
                    f"[VOICE DEBUG] TTS started: {message}"
                )

            self._engine.say(message)
            self._engine.runAndWait()

            if self.debug:
                print(
                    f"[VOICE DEBUG] TTS completed: {message}"
                )

        except Exception as exc:
            print(f"[VOICE ERROR] TTS failed: {exc}")

    def is_running(self):
        """Return True if the worker thread is running."""
        return (
            self._thread is not None
            and self._thread.is_alive()
        )

    def wait_until_empty(self, timeout=10):
        """
        Wait until the speech queue becomes empty.

        Returns True if empty before timeout.
        """
        start = time.time()

        while time.time() - start < timeout:
            if self.queue.size() == 0:
                return True

            time.sleep(0.05)

        return self.queue.size() == 0