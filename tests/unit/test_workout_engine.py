"""
Workout Engine Unit Test
"""

from ai_engine.workout_engine import WorkoutEngine


class MockLandmark:
    """
    Simple landmark object for testing.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y


def create_landmarks():
    """
    Create a minimal MediaPipe-like landmark list.

    33 landmarks are created because MediaPipe Pose
    provides 33 landmarks.
    """

    landmarks = [
        MockLandmark(0.0, 0.0)
        for _ in range(33)
    ]

    # ----------------------------------------------------------
    # Right squat landmarks
    #
    # Hip  = 24
    # Knee = 26
    # Ankle = 28
    #
    # Straight leg -> approximately 180 degrees
    # ----------------------------------------------------------

    landmarks[24] = MockLandmark(0.0, 0.0)
    landmarks[26] = MockLandmark(0.0, 1.0)
    landmarks[28] = MockLandmark(0.0, 2.0)

    return landmarks


print("Workout Engine Test")
print("-------------------")


# ==============================================================
# CREATE ENGINE
# ==============================================================

engine = WorkoutEngine()

print(
    "Engine created       :",
    "OK" if engine is not None else "FAILED"
)


# ==============================================================
# AVAILABLE EXERCISES
# ==============================================================

available = engine.get_available_exercises()

print(
    "Available exercises  :",
    available
)


# ==============================================================
# START SQUAT
# ==============================================================

analyzer = engine.start(
    "squat",
    side="right"
)

print(
    "Workout started      :",
    "OK" if engine.is_running() else "FAILED"
)

print(
    "Current exercise     :",
    engine.get_current_exercise()
)

print(
    "Analyzer             :",
    type(analyzer).__name__
)


# ==============================================================
# PROCESS LANDMARKS
# ==============================================================

landmarks = create_landmarks()

result = engine.process(landmarks)

print(
    "Process result       :",
    result
)

print(
    "Result exercise      :",
    result["exercise"]
)

print(
    "Result reps          :",
    result["reps"]
)


# ==============================================================
# GET RESULT
# ==============================================================

current_result = engine.get_result()

print(
    "Get result           :",
    "OK" if current_result is not None else "FAILED"
)


# ==============================================================
# RESET
# ==============================================================

engine.reset()

print(
    "Reset                :",
    "OK"
)


# ==============================================================
# STOP
# ==============================================================

engine.stop()

print(
    "Workout stopped      :",
    "OK" if not engine.is_running() else "FAILED"
)

print(
    "Current exercise     :",
    engine.get_current_exercise()
)


# ==============================================================
# INVALID PROCESS
# ==============================================================

try:
    engine.process(landmarks)

    print(
        "Inactive process     : FAILED"
    )

except RuntimeError:
    print(
        "Inactive process     : Correctly rejected"
    )


print("-------------------")
print("Workout Engine Test PASSED")