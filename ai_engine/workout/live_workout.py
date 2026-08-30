"""
Live Workout Controller

Connects:
    Webcam frame
        ↓
    PoseEngine
        ↓
    WorkoutEngine
        ↓
    Exercise Analyzer

This class is responsible for turning raw webcam frames
into real-time workout analysis results.
"""

from ai_engine.pose_engine import PoseEngine
from ai_engine.workout.workout_engine import WorkoutEngine

from voice_engine.speech_queue import SpeechQueue
from voice_engine.speech_worker import SpeechWorker
from voice_engine.voice_controller import VoiceController


class LiveWorkout:
    """
    High-level controller for a live AI workout session.
    """

    def __init__(
        self,
        model_path="models/pose_landmarker.task",
        voice_enabled=True,
        voice_confidence=0.70,
        speech_rate=175,
        speech_volume=1.0,
        speech_queue_size=20,
        debug=False,
    ):
        self.pose_engine = PoseEngine(
            model_path=model_path
        )

        self.workout_engine = WorkoutEngine()

        self.voice_enabled = bool(voice_enabled)
        self.voice_confidence = float(voice_confidence)
        self.speech_rate = int(speech_rate)
        self.speech_volume = float(speech_volume)
        self.speech_queue_size = int(speech_queue_size)
        self.debug = bool(debug)

        self.speech_queue = None
        self.speech_worker = None
        self.voice_controller = None

        if self.voice_enabled:
            self.speech_queue = SpeechQueue(
                max_size=self.speech_queue_size,
            )

            self.speech_worker = SpeechWorker(
                self.speech_queue,
                rate=self.speech_rate,
                volume=self.speech_volume,
                debug=self.debug,
            )

            self.voice_controller = VoiceController(
                self.speech_queue,
                min_confidence=self.voice_confidence,
                debug=self.debug,
            )

        self.active = False

    # ==========================================================
    # START
    # ==========================================================

    def start(self, exercise_name, **kwargs):
        """
        Start a live workout.

        Example:
            live.start("squat", side="right")
        """

        self.workout_engine.start(
            exercise_name,
            **kwargs
        )

        if (
            self.voice_enabled
            and self.speech_worker is not None
        ):
            self.speech_worker.start()

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):
            self.voice_controller.announce_workout_started()

        self.active = True

        return self.get_status()

    # ==========================================================
    # PROCESS FRAME
    # ==========================================================

    def process_frame(self, frame):
        """
        Process one webcam frame.

        Pipeline:

            BGR frame
                ↓
            PoseEngine
                ↓
            landmarks
                ↓
            WorkoutEngine
                ↓
            analysis result
        """

        if not self.active:
            raise RuntimeError(
                "Live workout is not active. "
                "Call start() before process_frame()."
            )

        # ------------------------------------------------------
        # Pose detection
        # ------------------------------------------------------

        results = self.pose_engine.process_frame(frame)

        # ------------------------------------------------------
        # Extract first person's landmarks
        # ------------------------------------------------------

        landmarks = self.pose_engine.get_landmarks(
            results
        )

        # No person detected
        if landmarks is None:
            return {
                "detected": False,
                "exercise": self.workout_engine.get_current_exercise(),
                "angle": None,
                "reps": self._get_reps(),
                "state": "NO_POSE",
                "form": "Move into camera view",
            }

        # ------------------------------------------------------
        # Analyze exercise
        # ------------------------------------------------------

        analysis = self.workout_engine.process(
            landmarks
        )

        result = {
            "detected": True,
            **analysis,
        }

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):
            try:
                self.voice_controller.process(result)
            except Exception as error:
                print(f"Voice controller error: {error}")

        # ------------------------------------------------------
        # Add detection status
        # ------------------------------------------------------

        return result

    # ==========================================================
    # STATUS
    # ==========================================================

    def get_status(self):
        """
        Return the current workout status.
        """

        return {
            "active": self.active,
            "exercise": (
                self.workout_engine.get_current_exercise()
            ),
            "result": self.workout_engine.get_result(),
        }

    # ==========================================================
    # REP COUNT
    # ==========================================================

    def _get_reps(self):
        """
        Safely return current repetition count.
        """

        result = self.workout_engine.get_result()

        if result is None:
            return 0

        return result.get("reps", 0)

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset the current workout.

        Exercise selection remains active.
        """

        if not self.active:
            return

        self.workout_engine.reset()

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):
        """
        Stop the workout and release the pose engine.
        """

        self.workout_engine.stop()

        if (
            self.voice_enabled
            and self.voice_controller is not None
        ):
            try:
                self.voice_controller.announce_workout_stopped()
            except Exception:
                pass

        if self.speech_worker is not None:
            try:
                self.speech_worker.stop()
            except Exception:
                pass

        self.active = False

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close(self):
        """
        Release all resources.

        Call this when the application exits.
        """

        self.stop()

        if self.pose_engine is not None:
            try:
                self.pose_engine.close()
            except Exception:
                pass
            self.pose_engine = None

    # ==========================================================
    # IS ACTIVE
    # ==========================================================

    def is_running(self):
        """
        Return whether a live workout is active.
        """

        return self.active