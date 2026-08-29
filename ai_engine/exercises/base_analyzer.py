"""
Base Exercise Analyzer

Defines the common interface that every exercise analyzer
should follow.
"""


class BaseExerciseAnalyzer:
    """
    Common interface for all exercise analyzers.
    """

    exercise_name = "unknown"

    def analyze(self, *args, **kwargs):
        """
        Analyze one frame / movement.

        Each exercise must implement this method.
        """
        raise NotImplementedError(
            "Exercise analyzer must implement analyze()."
        )

    def get_result(self):
        """
        Return the latest analysis result in a consistent format.
        """
        raise NotImplementedError(
            "Exercise analyzer must implement get_result()."
        )