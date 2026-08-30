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


class LiveWorkout:
    """
    High-level controller for a live AI workout session.
    """

    def __init__(
        self,
        model_path="models/pose_landmarker.task",
    ):
        self.pose_engine = PoseEngine(
            model_path=model_path
        )

        self.workout_engine = WorkoutEngine()

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

        # ------------------------------------------------------
        # Add detection status
        # ------------------------------------------------------

        return {
            "detected": True,
            **analysis,
        }

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

        self.pose_engine.close()

    # ==========================================================
    # IS ACTIVE
    # ==========================================================

    def is_running(self):
        """
        Return whether a live workout is active.
        """

        return self.active