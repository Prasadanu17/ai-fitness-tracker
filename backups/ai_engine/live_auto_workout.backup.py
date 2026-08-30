"""
Live Automatic Workout

Connects:

    Webcam
        ↓
    PoseEngine
        ↓
    Landmark Validation
        ↓
    WorkoutEngine.process_auto()
        ↓
    Automatic Exercise Detection
        ↓
    Exercise Analyzer
        ↓
    Standard Workout Result
        ↓
    VoiceController
        ↓
    SpeechQueue
        ↓
    SpeechWorker
        ↓
    Text-to-Speech

Responsibilities:
    - Open webcam
    - Run MediaPipe pose detection
    - Validate landmarks
    - Run automatic workout detection
    - Manage workout lifecycle
    - Optionally connect voice feedback
"""

import cv2

from ai_engine.pose_engine import PoseEngine
from ai_engine.workout.workout_engine import WorkoutEngine

from voice_engine.speech_queue import SpeechQueue
from voice_engine.speech_worker import SpeechWorker
from voice_engine.voice_controller import VoiceController


class LiveAutoWorkout:
    """
    Real-time automatic workout controller.

    Voice is optional.

    AI processing remains independent from the voice layer.
    """

    def __init__(
        self,
        camera_index=0,
        model_path="models/pose_landmarker.task",
        voice_enabled=False,
        voice_confidence=0.70,
        speech_rate=175,
        speech_volume=1.0,
        speech_queue_size=20,
    ):
        self.camera_index = camera_index
        self.model_path = model_path

        self.camera = None

        # ------------------------------------------------------
        # AI engines
        # ------------------------------------------------------

        self.pose_engine = PoseEngine(
            model_path=model_path
        )

        self.workout_engine = WorkoutEngine()

        self.running = False

        self.last_result = self._waiting_result()

        # ------------------------------------------------------
        # Voice configuration
        # ------------------------------------------------------

        self.voice_enabled = bool(
            voice_enabled
        )

        self.voice_confidence = float(
            voice_confidence
        )

        self.speech_rate = speech_rate
        self.speech_volume = speech_volume
        self.speech_queue_size = speech_queue_size

        # ------------------------------------------------------
        # Voice components
        # ------------------------------------------------------

        self.speech_queue = None
        self.speech_worker = None
        self.voice_controller = None

        if self.voice_enabled:

            self.speech_queue = SpeechQueue(
                max_size=self.speech_queue_size
            )

            self.speech_worker = SpeechWorker(
                speech_queue=self.speech_queue,
                rate=self.speech_rate,
                volume=self.speech_volume,
            )

            self.voice_controller = VoiceController(
                speech_queue=self.speech_queue,
                min_confidence=self.voice_confidence,
            )

    # ==========================================================
    # START
    # ==========================================================

    def start(self):
        """
        Start webcam, workout engine and optional voice worker.
        """

        if self.running:
            return True

        self.camera = cv2.VideoCapture(
            self.camera_index
        )

        if not self.camera.isOpened():

            self.camera.release()
            self.camera = None

            raise RuntimeError(
                "Unable to open webcam."
            )

        self.workout_engine.start_auto()

        # ------------------------------------------------------
        # Start speech worker
        # ------------------------------------------------------

        if (
            self.voice_enabled
            and self.speech_worker is not None
        ):

            self.speech_worker.start()

        self.running = True

        # ------------------------------------------------------
        # Announce workout started
        # ------------------------------------------------------

        if (
            self.voice_enabled
            and self.speech_queue is not None
        ):

            from voice_engine.voice_events import (
                workout_started,
            )

            self.speech_queue.put(
                workout_started()
            )

        return True

    # ==========================================================
    # PROCESS FRAME
    # ==========================================================

    def process_frame(self, frame):
        """
        Process one webcam frame safely.
        """

        if self.pose_engine is None:
            raise RuntimeError(
                "Pose engine is not initialized."
            )

        if self.workout_engine is None:
            raise RuntimeError(
                "Workout engine is not initialized."
            )

        # ------------------------------------------------------
        # Invalid frame
        # ------------------------------------------------------

        if frame is None:

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        # ------------------------------------------------------
        # Validate frame
        # ------------------------------------------------------

        if not hasattr(frame, "shape"):

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        if len(frame.shape) != 3:

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        height, width = frame.shape[:2]

        if height <= 0 or width <= 0:

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        # ------------------------------------------------------
        # MediaPipe
        # ------------------------------------------------------

        pose_results = self.pose_engine.process_frame(
            frame
        )

        if pose_results is None:

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        # ------------------------------------------------------
        # Extract landmarks
        # ------------------------------------------------------

        landmarks = self.pose_engine.get_landmarks(
            pose_results
        )

        if landmarks is None:

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        # ------------------------------------------------------
        # Landmark count
        # ------------------------------------------------------

        if len(landmarks) < 33:

            result = self._waiting_result()

            self.last_result = result

            self._process_voice(result)

            return result

        # ------------------------------------------------------
        # Required landmarks
        # ------------------------------------------------------

        required_indexes = [
            11, 12,
            13, 14,
            15, 16,
            23, 24,
            25, 26,
            27, 28,
        ]

        for index in required_indexes:

            landmark = landmarks[index]

            if landmark is None:

                result = self._waiting_result()

                self.last_result = result

                self._process_voice(result)

                return result

            if not hasattr(landmark, "x"):

                result = self._waiting_result()

                self.last_result = result

                self._process_voice(result)

                return result

            if not hasattr(landmark, "y"):

                result = self._waiting_result()

                self.last_result = result

                self._process_voice(result)

                return result

        # ------------------------------------------------------
        # Automatic workout processing
        # ------------------------------------------------------

        try:

            result = self.workout_engine.process_auto(
                landmarks
            )

        except RuntimeError:

            result = self._waiting_result()

        self.last_result = result

        # ------------------------------------------------------
        # Voice processing
        # ------------------------------------------------------

        self._process_voice(result)

        return result

    # ==========================================================
    # VOICE PROCESSING
    # ==========================================================

    def _process_voice(self, result):
        """
        Send workout results to VoiceController.

        Voice processing never affects the AI result.
        """

        if not self.voice_enabled:
            return

        if self.voice_controller is None:
            return

        try:

            self.voice_controller.process(
                result
            )

        except Exception as error:

            print(
                f"Voice controller error: {error}"
            )

    # ==========================================================
    # WAITING RESULT
    # ==========================================================

    def _waiting_result(self):
        """
        Standard result when no usable pose exists.
        """

        return {
            "exercise": None,
            "detected_exercise": None,
            "confidence": 0.0,
            "side": None,
            "status": "waiting",
            "reps": 0,
            "state": None,
            "form": None,
        }

    # ==========================================================
    # GET RESULT
    # ==========================================================

    def get_result(self):
        """
        Return the latest workout result.
        """

        return self.last_result

    # ==========================================================
    # RUN LIVE WORKOUT
    # ==========================================================

    def run(self):
        """
        Run the complete live webcam workout.

        Controls:

            Q = quit
            R = reset
        """

        self.start()

        print(
            "Live Automatic Workout"
        )

        print(
            "----------------------"
        )

        print(
            "Camera started : OK"
        )

        print(
            "Automatic detection enabled"
        )

        print(
            "Voice enabled  : "
            + ("YES" if self.voice_enabled else "NO")
        )

        print(
            "Press Q to quit"
        )

        print(
            "Press R to reset"
        )

        try:

            while self.running:

                success, frame = (
                    self.camera.read()
                )

                if not success:

                    print(
                        "Warning: unable to "
                        "read camera frame."
                    )

                    continue

                # --------------------------------------------------
                # AI
                # --------------------------------------------------

                result = self.process_frame(
                    frame
                )

                # --------------------------------------------------
                # UI
                # --------------------------------------------------

                self._draw_status(
                    frame,
                    result
                )

                cv2.imshow(
                    "AI Fitness Tracker",
                    frame
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break

                if key == ord("r"):
                    self.reset()

        finally:

            self.stop()

    # ==========================================================
    # SCREEN STATUS
    # ==========================================================

    def _draw_status(
        self,
        frame,
        result,
    ):
        """
        Draw basic live workout information.
        """

        exercise = result.get(
            "exercise"
        )

        reps = result.get(
            "reps",
            0
        )

        confidence = result.get(
            "confidence",
            0.0
        )

        status = result.get(
            "status",
            "waiting"
        )

        exercise_text = (
            exercise.replace("_", " ")
            if exercise
            else "Waiting..."
        )

        cv2.putText(
            frame,
            f"Exercise: {exercise_text}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Reps: {reps}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Confidence: {confidence:.2f}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"Status: {status}",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        if self.voice_enabled:

            cv2.putText(
                frame,
                "Voice: ON",
                (20, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset the current workout.
        """

        self.workout_engine.reset()

        self.last_result = (
            self._waiting_result()
        )

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):

            self.voice_controller.reset()

        if (
            self.voice_enabled
            and self.speech_queue is not None
        ):

            from voice_engine.voice_events import (
                workout_reset,
            )

            self.speech_queue.put(
                workout_reset()
            )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):
        """
        Stop webcam, workout and speech safely.
        """

        was_running = self.running

        self.running = False

        # ------------------------------------------------------
        # Workout stopped voice event
        # ------------------------------------------------------

        if (
            was_running
            and self.voice_enabled
            and self.speech_queue is not None
        ):

            from voice_engine.voice_events import (
                workout_stopped,
            )

            self.speech_queue.put(
                workout_stopped()
            )

        # ------------------------------------------------------
        # Camera
        # ------------------------------------------------------

        if self.camera is not None:

            self.camera.release()

            self.camera = None

        # ------------------------------------------------------
        # Workout
        # ------------------------------------------------------

        if self.workout_engine is not None:

            self.workout_engine.stop()

        # ------------------------------------------------------
        # Voice
        # ------------------------------------------------------

        if self.speech_worker is not None:

            try:

                self.speech_worker.stop(
                    timeout=2.0
                )

            except Exception as error:

                print(
                    f"Speech stop error: {error}"
                )

        cv2.destroyAllWindows()

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Release all resources.
        """

        self.stop()

        if self.pose_engine is not None:

            self.pose_engine.close()

            self.pose_engine = None

        self.speech_worker = None
        self.voice_controller = None
        self.speech_queue = None