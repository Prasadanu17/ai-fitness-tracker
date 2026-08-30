"""
Live Exercise Engine Integration Test

Tests the complete analyzer-selection pipeline
without opening the webcam.

Pipeline:

Exercise Selection
        ↓
Analyzer Creation
        ↓
Landmarks
        ↓
Exercise Analysis
        ↓
Result
"""

from ai_engine.workout.live_exercise_engine import LiveExerciseEngine


class Landmark:
    """
    Minimal MediaPipe-like landmark object.
    """

    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def create_landmarks():
    """
    Create 33 placeholder landmarks.

    MediaPipe Pose provides 33 landmarks.
    """

    return [
        Landmark(0.0, 0.0)
        for _ in range(33)
    ]


def set_landmark(
    landmarks,
    index,
    x,
    y
):
    landmarks[index] = Landmark(x, y)


# ==========================================================
# TEST
# ==========================================================

print("Live Exercise Engine Test")
print("--------------------------")


engine = LiveExerciseEngine(
    exercise="squat",
    side="right"
)

print(
    "Selected exercise:",
    engine.get_current_exercise()
)

print(
    "Analyzer:",
    type(engine.get_analyzer()).__name__
)


# ----------------------------------------------------------
# Verify exercise switching
# ----------------------------------------------------------

engine.select_exercise(
    "lunge",
    side="right"
)

print(
    "Switched exercise:",
    engine.get_current_exercise()
)

print(
    "Analyzer:",
    type(engine.get_analyzer()).__name__
)


# ----------------------------------------------------------
# Verify another switch
# ----------------------------------------------------------

engine.select_exercise(
    "bicep_curl",
    side="right"
)

print(
    "Switched exercise:",
    engine.get_current_exercise()
)

print(
    "Analyzer:",
    type(engine.get_analyzer()).__name__
)


# ----------------------------------------------------------
# Clear
# ----------------------------------------------------------

engine.clear_exercise()

print(
    "After clear:",
    engine.get_current_exercise()
)

print("--------------------------")
print("Live Exercise Engine Test PASSED")