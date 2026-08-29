"""
Exercise Registry

Central registry for all supported exercises.

This module provides a single place to register and retrieve
exercise analyzers, making the AI Fitness Engine easy to extend.
"""

from ai_engine.exercises.squat import SquatAnalyzer
from ai_engine.exercises.bicep_curl import BicepCurlAnalyzer


# -------------------------------------------------------------------
# Exercise Registry
# -------------------------------------------------------------------

EXERCISE_REGISTRY = {
    "squat": SquatAnalyzer,
    "bicep_curl": BicepCurlAnalyzer,
}


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def get_exercise_analyzer(exercise_name, **kwargs):
    """
    Create and return an analyzer for the requested exercise.

    Parameters
    ----------
    exercise_name : str
        Name of the exercise, e.g. "squat" or "bicep_curl".

    **kwargs
        Optional configuration passed to the analyzer.

    Returns
    -------
    object
        Initialized exercise analyzer.

    Raises
    ------
    ValueError
        If the exercise is not supported.
    """

    if not isinstance(exercise_name, str):
        raise ValueError("Exercise name must be a string.")

    exercise_name = exercise_name.strip().lower()

    if exercise_name not in EXERCISE_REGISTRY:
        available = ", ".join(EXERCISE_REGISTRY.keys())

        raise ValueError(
            f"Unsupported exercise: '{exercise_name}'. "
            f"Available exercises: {available}"
        )

    analyzer_class = EXERCISE_REGISTRY[exercise_name]

    return analyzer_class(**kwargs)


def get_available_exercises():
    """
    Return a list of all supported exercise names.
    """

    return list(EXERCISE_REGISTRY.keys())


def is_exercise_supported(exercise_name):
    """
    Check whether an exercise is supported.
    """

    if not isinstance(exercise_name, str):
        return False

    return exercise_name.strip().lower() in EXERCISE_REGISTRY