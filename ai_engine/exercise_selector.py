"""
Exercise Selector

Provides a clean interface for selecting an exercise analyzer.
The selector uses the central Exercise Registry rather than
directly importing individual exercise implementations.
"""

from ai_engine.exercise_registry import (
    get_available_exercises,
    get_exercise_analyzer,
    is_exercise_supported,
)


class ExerciseSelector:
    """
    Selects and manages the active exercise analyzer.
    """

    def __init__(self):
        self.current_exercise = None
        self.current_analyzer = None

    def select(self, exercise_name, **kwargs):
        """
        Select an exercise and create its analyzer.

        Parameters
        ----------
        exercise_name : str
            Exercise to select.

        **kwargs
            Configuration passed to the analyzer.

        Returns
        -------
        object
            The selected exercise analyzer.
        """

        if not is_exercise_supported(exercise_name):
            available = ", ".join(get_available_exercises())

            raise ValueError(
                f"Unsupported exercise: '{exercise_name}'. "
                f"Available exercises: {available}"
            )

        self.current_exercise = exercise_name.strip().lower()

        self.current_analyzer = get_exercise_analyzer(
            self.current_exercise,
            **kwargs
        )

        return self.current_analyzer

    def get_current_exercise(self):
        """
        Return the currently selected exercise.
        """
        return self.current_exercise

    def get_current_analyzer(self):
        """
        Return the currently active analyzer.
        """
        return self.current_analyzer

    def clear(self):
        """
        Clear the current exercise selection.
        """
        self.current_exercise = None
        self.current_analyzer = None

    def get_available_exercises(self):
        """
        Return all available exercises.
        """
        return get_available_exercises()