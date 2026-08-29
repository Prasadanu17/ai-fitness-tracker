"""
Workout Engine

Central orchestration layer for the AI Fitness Tracker.

Responsibilities:
    - Start a workout with a selected exercise.
    - Manage the active exercise analyzer.
    - Process MediaPipe pose landmarks.
    - Return standardized workout results.
    - Reset and stop workouts safely.

Architecture:

    PoseEngine
        |
        v
    WorkoutEngine
        |
        v
    ExerciseSelector
        |
        +---- SquatAnalyzer
        |
        +---- BicepCurlAnalyzer
        |
        +---- LungeAnalyzer
"""


from ai_engine.exercise_selector import ExerciseSelector


class WorkoutEngine:
    """
    Central controller for exercise analysis.

    The WorkoutEngine does not directly import individual
    exercise analyzers. It delegates exercise selection to
    ExerciseSelector.
    """

    def __init__(self):
        self.selector = ExerciseSelector()

        self.is_active = False
        self.session_id = None

    # ==========================================================
    # START WORKOUT
    # ==========================================================

    def start(self, exercise_name, **kwargs):
        """
        Start a workout for the selected exercise.

        Parameters
        ----------
        exercise_name : str
            Exercise name, for example:
                "squat"
                "bicep_curl"
                "lunge"

        **kwargs
            Configuration passed to the analyzer.

            Example:
                side="right"

        Returns
        -------
        object
            The selected exercise analyzer.
        """

        analyzer = self.selector.select(
            exercise_name,
            **kwargs
        )

        self.is_active = True

        return analyzer

    # ==========================================================
    # PROCESS FRAME
    # ==========================================================

    def process(self, landmarks):
        """
        Process one frame of MediaPipe pose landmarks.

        Parameters
        ----------
        landmarks
            MediaPipe pose landmarks.

        Returns
        -------
        dict
            Standardized exercise analysis result.

        Raises
        ------
        RuntimeError
            If no workout is currently active.
        """

        if not self.is_active:
            raise RuntimeError(
                "No active workout. "
                "Call start() before process()."
            )

        analyzer = self.selector.get_current_analyzer()

        if analyzer is None:
            raise RuntimeError(
                "Workout is active but no analyzer is selected."
            )

        return analyzer.analyze(landmarks)

    # ==========================================================
    # CURRENT RESULT
    # ==========================================================

    def get_result(self):
        """
        Return the current analyzer result.

        Returns
        -------
        dict or None
            Current workout result.

        Returns None if no workout is active.
        """

        if not self.is_active:
            return None

        analyzer = self.selector.get_current_analyzer()

        if analyzer is None:
            return None

        return analyzer.get_result()

    # ==========================================================
    # CURRENT EXERCISE
    # ==========================================================

    def get_current_exercise(self):
        """
        Return the currently active exercise.

        Returns
        -------
        str or None
        """

        return self.selector.get_current_exercise()

    # ==========================================================
    # CURRENT ANALYZER
    # ==========================================================

    def get_current_analyzer(self):
        """
        Return the currently active analyzer.

        Returns
        -------
        object or None
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
    # STOP WORKOUT
    # ==========================================================

    def stop(self):
        """
        Stop the current workout.

        The selected exercise and analyzer are cleared.
        """

        self.selector.clear()
        self.is_active = False
        self.session_id = None

    # ==========================================================
    # RESET WORKOUT
    # ==========================================================

    def reset(self):
        """
        Reset the current analyzer without changing
        the selected exercise.

        Useful when the user wants to restart rep counting
        during the same exercise.
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