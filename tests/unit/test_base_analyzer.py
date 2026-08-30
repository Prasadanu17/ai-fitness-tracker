"""
Tests for BaseExerciseAnalyzer.

The base analyzer is intentionally abstract and therefore
cannot be instantiated directly.
"""

from ai_engine.exercises.base_exercise_analyzer import (
    BaseExerciseAnalyzer,
)


print("Base Exercise Analyzer Test")
print("---------------------------")


# ==========================================================
# ABSTRACT CLASS TEST
# ==========================================================

try:
    BaseExerciseAnalyzer()

    raise AssertionError(
        "BaseExerciseAnalyzer should be abstract."
    )

except TypeError:
    print("Abstract protection    : OK")


# ==========================================================
# DUMMY CONCRETE IMPLEMENTATION
# ==========================================================

class DummyExerciseAnalyzer(BaseExerciseAnalyzer):
    """
    Minimal concrete analyzer used to verify the base
    analyzer contract.
    """

    def __init__(self):
        self.result = {
            "exercise": "dummy",
            "reps": 0,
            "confidence": 0.0,
        }

    # ------------------------------------------------------
    # ANALYZE
    # ------------------------------------------------------

    def analyze(self, landmarks):
        """
        Analyze a frame.

        This dummy implementation simply returns the
        current result.
        """

        return self.result

    # ------------------------------------------------------
    # GET RESULT
    # ------------------------------------------------------

    def get_result(self):
        """
        Return the current result.
        """

        return self.result

    # ------------------------------------------------------
    # RESET
    # ------------------------------------------------------

    def reset(self):
        """
        Reset the dummy analyzer.
        """

        self.result = {
            "exercise": "dummy",
            "reps": 0,
            "confidence": 0.0,
        }


# ==========================================================
# CONCRETE IMPLEMENTATION TEST
# ==========================================================

analyzer = DummyExerciseAnalyzer()

assert isinstance(
    analyzer,
    BaseExerciseAnalyzer,
)

print("Concrete implementation : OK")


# ==========================================================
# ANALYZE TEST
# ==========================================================

result = analyzer.analyze([])

assert isinstance(result, dict)

assert result["exercise"] == "dummy"

assert result["reps"] == 0

assert result["confidence"] == 0.0

print("analyze() interface     : OK")


# ==========================================================
# GET RESULT TEST
# ==========================================================

result = analyzer.get_result()

assert isinstance(result, dict)

assert result["exercise"] == "dummy"

print("get_result() interface  : OK")


# ==========================================================
# RESET TEST
# ==========================================================

analyzer.result["reps"] = 5

assert analyzer.result["reps"] == 5

analyzer.reset()

assert analyzer.result["reps"] == 0

print("reset() interface       : OK")


# ==========================================================
# FINAL
# ==========================================================

print("---------------------------")
print("Base Analyzer Test PASSED")