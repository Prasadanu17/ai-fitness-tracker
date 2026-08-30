"""
Base Exercise Analyzer

Defines the common abstract interface that every
exercise analyzer must implement.

All exercise-specific analyzers such as:

    - SquatAnalyzer
    - BicepCurlAnalyzer
    - LungeAnalyzer

should inherit from this class.
"""

from abc import ABC, abstractmethod


class BaseExerciseAnalyzer(ABC):
    """
    Common interface for all exercise analyzers.

    Every exercise analyzer must implement:

        - analyze()
        - get_result()
        - reset()
    """

    # ==========================================================
    # ANALYZE
    # ==========================================================

    @abstractmethod
    def analyze(self, landmarks):
        """
        Analyze one frame of pose landmarks.

        Parameters
        ----------
        landmarks:
            MediaPipe pose landmarks for the current frame.

        Returns
        -------
        dict
            Standardized exercise analysis result.

        Notes
        -----
        Each exercise analyzer is responsible for implementing
        its own movement and form analysis logic.
        """

        raise NotImplementedError(
            "Exercise analyzer must implement analyze()."
        )

    # ==========================================================
    # GET RESULT
    # ==========================================================

    @abstractmethod
    def get_result(self):
        """
        Return the latest standardized analysis result.

        Returns
        -------
        dict
            Current exercise analysis state.
        """

        raise NotImplementedError(
            "Exercise analyzer must implement get_result()."
        )

    # ==========================================================
    # RESET
    # ==========================================================

    @abstractmethod
    def reset(self):
        """
        Reset the analyzer state.

        This should clear temporary movement state,
        repetition counters, feedback state, and any
        exercise-specific tracking information.
        """

        raise NotImplementedError(
            "Exercise analyzer must implement reset()."
        )