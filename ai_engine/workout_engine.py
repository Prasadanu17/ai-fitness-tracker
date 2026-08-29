"""
Workout Engine

Central orchestration layer for the AI Fitness Tracker.

Responsibilities:
    - Start a workout with a selected exercise.
    - Start a workout in automatic detection mode.
    - Manage the active exercise analyzer.
    - Process MediaPipe pose landmarks.
    - Automatically detect and switch exercises.
    - Return standardized workout results.
    - Reset and stop workouts safely.

Architecture:

    PoseEngine
        |
        v
    WorkoutEngine
        |
        +---- Manual Mode
        |       |
        |       v
        |   ExerciseSelector
        |
        +---- Automatic Mode
                |
                v
        ExerciseDetector
                |
                v
        ExerciseSelector
                |
        +-------+-------+-------+
        |       |       |
        v       v       v
      Squat   Curl    Lunge
      Analyzer Analyzer Analyzer
"""


from ai_engine.exercise_detector import ExerciseDetector
from ai_engine.exercise_selector import ExerciseSelector


class WorkoutEngine:
    """
    Central controller for exercise analysis.

    Supports two modes:

        Manual:
            start("squat")

        Automatic:
            start_auto()
            process_auto(landmarks)

    Individual exercise analyzers are managed through
    ExerciseSelector.
    """

    def __init__(self):
        self.selector = ExerciseSelector()
        self.detector = ExerciseDetector()

        self.is_active = False
        self.session_id = None

        # True when automatic exercise detection is enabled.
        self.auto_detect = False

        # Exercise currently detected by ExerciseDetector.
        self.detected_exercise = None

    # ==========================================================
    # MANUAL START
    # ==========================================================

    def start(self, exercise_name, **kwargs):
        """
        Start a manually selected workout.

        Example:
            start("squat", side="right")
        """

        analyzer = self.selector.select(
            exercise_name,
            **kwargs
        )

        self.is_active = True
        self.auto_detect = False

        self.detected_exercise = None

        return analyzer

    # ==========================================================
    # AUTOMATIC START
    # ==========================================================

    def start_auto(self):
        """
        Start workout in automatic exercise-detection mode.

        The exercise will be selected automatically when
        pose landmarks are processed.
        """

        self.selector.clear()

        self.detector.reset()

        self.is_active = True
        self.auto_detect = True

        self.detected_exercise = None

        return True

    # ==========================================================
    # MANUAL PROCESS
    # ==========================================================

    def process(self, landmarks):
        """
        Process one frame using the manually selected analyzer.

        Raises:
            RuntimeError if no workout is active.
        """

        if not self.is_active:
            raise RuntimeError(
                "No active workout. "
                "Call start() before process()."
            )

        if self.auto_detect:
            raise RuntimeError(
                "Workout is running in automatic mode. "
                "Call process_auto() instead."
            )

        analyzer = self.selector.get_current_analyzer()

        if analyzer is None:
            raise RuntimeError(
                "Workout is active but no analyzer is selected."
            )

        return analyzer.analyze(landmarks)

    # ==========================================================
    # AUTOMATIC PROCESS
    # ==========================================================

    def process_auto(self, landmarks):
        """
        Process one frame using automatic exercise detection.

        Flow:

            landmarks
                ↓
            ExerciseDetector
                ↓
            detected exercise
                ↓
            ExerciseSelector
                ↓
            correct analyzer
                ↓
            analysis result
        """

        if not self.is_active:
            raise RuntimeError(
                "No active workout. "
                "Call start_auto() before process_auto()."
            )

        if not self.auto_detect:
            raise RuntimeError(
                "Workout is not running in automatic mode."
            )

        # ------------------------------------------------------
        # Detect exercise
        # ------------------------------------------------------

        detection = self.detector.detect(landmarks)

        exercise = detection["exercise"]
        confidence = detection["confidence"]
        side = detection["side"]

        # ------------------------------------------------------
        # Nothing detected
        # ------------------------------------------------------

        if exercise is None:

            return {
                "exercise": None,
                "confidence": confidence,
                "side": None,
                "status": "waiting_for_exercise",
            }

        # ------------------------------------------------------
        # Exercise changed
        # ------------------------------------------------------

        if exercise != self.detected_exercise:

            self.selector.select(
                exercise,
                side=side,
            )

            self.detected_exercise = exercise

        # ------------------------------------------------------
        # Analyze using selected analyzer
        # ------------------------------------------------------

        analyzer = self.selector.get_current_analyzer()

        if analyzer is None:
            raise RuntimeError(
                "Exercise was detected but analyzer could not "
                "be created."
            )

        result = analyzer.analyze(landmarks)

        # Add automatic-detection information.
        result["confidence"] = confidence
        result["detection_mode"] = "automatic"

        return result

    # ==========================================================
    # CURRENT RESULT
    # ==========================================================

    def get_result(self):
        """
        Return the current analyzer result.

        Returns:
            dict or None
        """

        if not self.is_active:
            return None

        analyzer = self.selector.get_current_analyzer()

        if analyzer is None:
            return None

        result = analyzer.get_result()

        if self.auto_detect:
            result["confidence"] = self.detector.get_confidence()
            result["detection_mode"] = "automatic"

        return result

    # ==========================================================
    # CURRENT EXERCISE
    # ==========================================================

    def get_current_exercise(self):
        """
        Return the currently selected exercise.
        """

        return self.selector.get_current_exercise()

    # ==========================================================
    # DETECTED EXERCISE
    # ==========================================================

    def get_detected_exercise(self):
        """
        Return the exercise currently detected automatically.
        """

        return self.detected_exercise

    # ==========================================================
    # DETECTION CONFIDENCE
    # ==========================================================

    def get_detection_confidence(self):
        """
        Return the latest exercise detection confidence.
        """

        return self.detector.get_confidence()

    # ==========================================================
    # CURRENT ANALYZER
    # ==========================================================

    def get_current_analyzer(self):
        """
        Return the currently active analyzer.
        """

        return self.selector.get_current_analyzer()

    # ==========================================================
    # AVAILABLE EXERCISES
    # ==========================================================

    def get_available_exercises(self):
        """
        Return all exercises supported by the registry.
        """

        return self.selector.get_available_exercises()

    # ==========================================================
    # WORKOUT MODE
    # ==========================================================

    def is_auto_mode(self):
        """
        Return True if automatic detection is enabled.
        """

        return self.auto_detect

    # ==========================================================
    # STOP WORKOUT
    # ==========================================================

    def stop(self):
        """
        Stop the current workout.

        Clears:
            - analyzer
            - exercise selection
            - detector state
            - automatic mode
        """

        self.selector.clear()

        self.detector.reset()

        self.is_active = False
        self.auto_detect = False

        self.detected_exercise = None
        self.session_id = None

    # ==========================================================
    # RESET WORKOUT
    # ==========================================================

    def reset(self):
        """
        Reset the current analyzer.

        The selected exercise is preserved.

        In automatic mode, the currently detected exercise
        is also preserved.
        """

        if not self.is_active:
            return

        analyzer = self.selector.get_current_analyzer()

        if analyzer is not None:
            analyzer.reset()

    # ==========================================================
    # WORKOUT STATUS
    # ==========================================================

    def is_running(self):
        """
        Return whether a workout is currently active.
        """

        return self.is_active