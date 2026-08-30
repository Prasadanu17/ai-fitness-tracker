from abc import ABC, abstractmethod


class ExerciseAnalyzer(ABC):
    """
    Base class for all exercise analyzers.

    Every exercise should implement:
        analyze()
        get_result()
        reset()
    """

    @abstractmethod
    def analyze(self, landmarks):
        """
        Analyze the current pose.

        Args:
            landmarks: MediaPipe pose landmarks

        Returns:
            dict containing exercise analysis results.
        """
        pass

    @abstractmethod
    def get_result(self):
        """
        Return the current exercise state/results.
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Reset the exercise analyzer.
        """
        pass