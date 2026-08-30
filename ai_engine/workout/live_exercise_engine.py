"""
Live Exercise Engine

Connects:
    PoseEngine
        ↓
    ExerciseSelector
        ↓
    Exercise Analyzer
        ↓
    Live Result

Supported exercises are provided by the Exercise Registry.
"""

from ai_engine.registry.exercise_selector import ExerciseSelector


class LiveExerciseEngine:
    """
    Coordinates live pose analysis for the selected exercise.

    The engine does NOT contain exercise-specific logic.

    Exercise-specific logic remains inside:
        SquatAnalyzer
        BicepCurlAnalyzer
        LungeAnalyzer
        ...

    This keeps the architecture modular.
    """

    def __init__(self, exercise="squat", side="right"):
        self.side = side
        self.selector = ExerciseSelector()

        self.select_exercise(
            exercise,
            side=side
        )

        self.last_result = None

    # ==========================================================
    # EXERCISE SELECTION
    # ==========================================================

    def select_exercise(self, exercise_name, **kwargs):
        """
        Select an exercise and create its analyzer.

        Example:
            engine.select_exercise("squat")

            engine.select_exercise(
                "lunge",
                side="left"
            )
        """

        if "side" not in kwargs:
            kwargs["side"] = self.side

        analyzer = self.selector.select(
            exercise_name,
            **kwargs
        )

        self.last_result = None

        return analyzer

    # ==========================================================
    # ANALYZE FRAME
    # ==========================================================

    def process_landmarks(self, landmarks):
        """
        Process one frame of MediaPipe landmarks.

        Parameters
        ----------
        landmarks:
            MediaPipe pose landmark collection.

        Returns
        -------
        dict:
            Current exercise result.
        """

        analyzer = self.selector.get_analyzer()

        if analyzer is None:
            raise RuntimeError(
                "No exercise selected."
            )

        self.last_result = analyzer.analyze(
            landmarks
        )

        return self.last_result

    # ==========================================================
    # RESULT
    # ==========================================================

    def get_result(self):
        """
        Return the latest analysis result.
        """

        if self.last_result is not None:
            return self.last_result

        analyzer = self.selector.get_analyzer()

        if analyzer is None:
            return None

        return analyzer.get_result()

    # ==========================================================
    # EXERCISE INFORMATION
    # ==========================================================

    def get_current_exercise(self):
        """
        Return currently selected exercise name.
        """

        return self.selector.get_selected_exercise()

    def get_analyzer(self):
        """
        Return the active exercise analyzer.
        """

        return self.selector.get_analyzer()

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset the active exercise analyzer.
        """

        analyzer = self.selector.get_analyzer()

        if analyzer is not None:
            analyzer.reset()

        self.last_result = None

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear_exercise(self):
        """
        Remove the currently selected exercise.
        """

        self.selector.clear()

        self.last_result = None