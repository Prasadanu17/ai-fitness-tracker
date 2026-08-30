"""
Exercise Selector

Provides a clean interface for selecting and managing
exercise analyzers.

The selector uses the central Exercise Registry instead of
directly importing individual exercise implementations.

This keeps the system modular and allows new exercises to be
added without changing the selector itself.

Compatibility methods are provided for older and newer
workout-engine components.
"""

from ai_engine.registry.exercise_registry import (
    get_available_exercises,
    get_exercise_analyzer,
    is_exercise_supported,
)


class ExerciseSelector:
    """
    Selects and manages the active exercise analyzer.

    Example
    -------
    selector = ExerciseSelector()

    analyzer = selector.select("squat", side="right")

    result = analyzer.analyze(landmarks)
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):
        """
        Initialize the selector with no active exercise.
        """

        self.current_exercise = None
        self.current_analyzer = None

    # ==========================================================
    # SELECT EXERCISE
    # ==========================================================

    def select(self, exercise_name, **kwargs):
        """
        Select an exercise and create its analyzer.

        Parameters
        ----------
        exercise_name : str
            Name of the exercise to select.

        **kwargs
            Configuration passed to the selected analyzer.

        Returns
        -------
        object
            The selected exercise analyzer.

        Raises
        ------
        TypeError
            If exercise_name is not a string.

        ValueError
            If exercise_name is empty or unsupported.
        """

        # ------------------------------------------------------
        # Validate exercise name type
        # ------------------------------------------------------

        if not isinstance(exercise_name, str):
            raise TypeError(
                "exercise_name must be a string"
            )

        # ------------------------------------------------------
        # Normalize exercise name
        # ------------------------------------------------------

        exercise_name = exercise_name.strip().lower()

        if not exercise_name:
            raise ValueError(
                "exercise_name cannot be empty"
            )

        # ------------------------------------------------------
        # Check registry
        # ------------------------------------------------------

        if not is_exercise_supported(exercise_name):

            available = ", ".join(
                get_available_exercises()
            )

            raise ValueError(
                f"Unsupported exercise: '{exercise_name}'. "
                f"Available exercises: {available}"
            )

        # ------------------------------------------------------
        # Create analyzer through central registry
        # ------------------------------------------------------

        analyzer = get_exercise_analyzer(
            exercise_name,
            **kwargs
        )

        # ------------------------------------------------------
        # Update state only after successful creation
        # ------------------------------------------------------

        self.current_exercise = exercise_name
        self.current_analyzer = analyzer

        return analyzer

    # ==========================================================
    # CURRENT EXERCISE
    # ==========================================================

    def get_current_exercise(self):
        """
        Return the currently selected exercise.

        Returns
        -------
        str or None
            Exercise name or None if nothing is selected.
        """

        return self.current_exercise

    # ==========================================================
    # SELECTED EXERCISE
    # ==========================================================

    def get_selected_exercise(self):
        """
        Compatibility alias for get_current_exercise().

        Returns
        -------
        str or None
            Currently selected exercise.
        """

        return self.get_current_exercise()

    # ==========================================================
    # CURRENT ANALYZER
    # ==========================================================

    def get_current_analyzer(self):
        """
        Return the currently active exercise analyzer.

        Returns
        -------
        object or None
            Active analyzer or None if no exercise is selected.
        """

        return self.current_analyzer

    # ==========================================================
    # SELECTED ANALYZER
    # ==========================================================

    def get_selected_analyzer(self):
        """
        Compatibility alias for get_current_analyzer().

        Returns
        -------
        object or None
            Active analyzer or None.
        """

        return self.get_current_analyzer()

    # ==========================================================
    # ANALYZER
    # ==========================================================

    def get_analyzer(self):
        """
        Compatibility alias for get_current_analyzer().

        Existing workout engines may call:

            selector.get_analyzer()

        This keeps the selector compatible with those components.

        Returns
        -------
        object or None
            Currently active analyzer.
        """

        return self.get_current_analyzer()

    # ==========================================================
    # SELECTION STATUS
    # ==========================================================

    def has_selection(self):
        """
        Check whether an exercise is currently selected.

        Returns
        -------
        bool
            True if an analyzer is active, otherwise False.
        """

        return self.current_analyzer is not None

    # ==========================================================
    # RESET CURRENT ANALYZER
    # ==========================================================

    def reset_current_analyzer(self):
        """
        Reset the currently selected analyzer without
        removing the exercise selection.

        Useful when starting a new workout session while
        keeping the same exercise selected.
        """

        if self.current_analyzer is None:
            return

        reset_method = getattr(
            self.current_analyzer,
            "reset",
            None,
        )

        if callable(reset_method):
            reset_method()

    # ==========================================================
    # CLEAR SELECTION
    # ==========================================================

    def clear(self):
        """
        Clear the current exercise selection and analyzer.
        """

        self.current_exercise = None
        self.current_analyzer = None

    # ==========================================================
    # AVAILABLE EXERCISES
    # ==========================================================

    def get_available_exercises(self):
        """
        Return all exercises registered in the system.

        Returns
        -------
        list[str]
            Available exercise names.
        """

        return get_available_exercises()