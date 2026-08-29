from abc import ABC, abstractmethod


class BaseExerciseAnalyzer(ABC):
    """
    Common interface for all exercise analyzers.

    Every exercise analyzer must implement:
        - analyze()
        - get_result()
        - reset()
    """

    @abstractmethod
    def analyze(self, landmarks):
        """
        Analyze one frame of pose landmarks.

        Returns:
            dict: Standardized exercise analysis result.
        """
        raise NotImplementedError

    @abstractmethod
    def get_result(self):
        """
        Return the latest standardized analysis result.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        """
        Reset analyzer state.
        """
        raise NotImplementedError