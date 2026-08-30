"""
Exercise Registry

Central registry for all supported exercises.

Supported:
    - squat
    - bicep_curl
    - lunge
"""

from ai_engine.exercises.squat import SquatAnalyzer
from ai_engine.exercises.bicep_curl import BicepCurlAnalyzer
from ai_engine.exercises.lunge import LungeAnalyzer


# ==========================================================
# REGISTRY
# ==========================================================

EXERCISE_REGISTRY = {
    "squat": SquatAnalyzer,
    "bicep_curl": BicepCurlAnalyzer,
    "lunge": LungeAnalyzer,
}


# ==========================================================
# AVAILABLE EXERCISES
# ==========================================================

def get_available_exercises():
    """
    Return all supported exercise names.
    """

    return list(EXERCISE_REGISTRY.keys())


# ==========================================================
# SUPPORT CHECK
# ==========================================================

def is_exercise_supported(exercise_name):
    """
    Check whether an exercise is supported.
    """

    if not isinstance(exercise_name, str):
        return False

    return exercise_name.lower() in EXERCISE_REGISTRY


# ==========================================================
# GET ANALYZER
# ==========================================================

def get_exercise_analyzer(exercise_name, **kwargs):
    """
    Create and return an analyzer instance.

    Example:

        analyzer = get_exercise_analyzer(
            "squat",
            side="right"
        )

    Returns:
        SquatAnalyzer instance
    """

    if not is_exercise_supported(exercise_name):
        raise ValueError(
            f"Unsupported exercise: {exercise_name}"
        )

    analyzer_class = EXERCISE_REGISTRY[
        exercise_name.lower()
    ]

    return analyzer_class(**kwargs)


# ==========================================================
# GET ANALYZER CLASS
# ==========================================================

def get_exercise_analyzer_class(exercise_name):
    """
    Return the analyzer class without creating an instance.
    """

    if not is_exercise_supported(exercise_name):
        raise ValueError(
            f"Unsupported exercise: {exercise_name}"
        )

    return EXERCISE_REGISTRY[
        exercise_name.lower()
    ]


# ==========================================================
# CLASS API
# ==========================================================

class ExerciseRegistry:
    """
    Object-oriented interface to the exercise registry.
    """

    @classmethod
    def get_available_exercises(cls):
        return get_available_exercises()

    @classmethod
    def is_supported(cls, exercise_name):
        return is_exercise_supported(exercise_name)

    @classmethod
    def get_analyzer_class(cls, exercise_name):
        return get_exercise_analyzer_class(exercise_name)

    @classmethod
    def create_analyzer(cls, exercise_name, **kwargs):
        return get_exercise_analyzer(
            exercise_name,
            **kwargs
        )