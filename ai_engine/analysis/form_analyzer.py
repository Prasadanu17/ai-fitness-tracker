"""
Form Analyzer

Provides a common interface for exercise form analysis.

The analyzer is intentionally separated from:
    - exercise detection
    - rep counting
    - workout orchestration

This allows form analysis to evolve independently.
"""


class FormAnalyzer:
    """
    Base interface for exercise form analysis.
    """

    def __init__(self):
        self.score = 0.0
        self.status = "Waiting"
        self.feedback = []

    def analyze(self, landmarks, exercise_result=None):
        """
        Analyze exercise form for the current frame.

        Parameters
        ----------
        landmarks
            MediaPipe pose landmarks.

        exercise_result : dict or None
            Result produced by the exercise analyzer.

        Returns
        -------
        dict
            Standardized form result.
        """

        raise NotImplementedError(
            "Subclasses must implement analyze()."
        )

    def get_result(self):
        """
        Return the latest form result.
        """

        return {
            "score": round(self.score, 1),
            "status": self.status,
            "feedback": list(self.feedback),
        }

    def reset(self):
        """
        Reset form state.
        """

        self.score = 0.0
        self.status = "Waiting"
        self.feedback = []