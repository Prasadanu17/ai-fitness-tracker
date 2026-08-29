"""
Auto Workout Switching Test

Tests automatic exercise switching through:

    ExerciseDetector
        ↓
    DetectionStabilizer
        ↓
    AutoWorkoutEngine
        ↓
    ExerciseSelector
"""


from ai_engine.auto_workout_engine import (
    AutoWorkoutEngine,
)


def make_landmark(x, y, z=0.0):
    return type(
        "Landmark",
        (),
        {
            "x": x,
            "y": y,
            "z": z,
            "visibility": 1.0,
        },
    )()


def create_landmarks():
    return [
        make_landmark(0.0, 0.0)
        for _ in range(33)
    ]


print("Auto Workout Switching Test")
print("----------------------------")

engine = AutoWorkoutEngine(
    confirmation_frames=3,
    minimum_confidence=0.60,
)

print("Engine created : OK")

assert engine.start() is True

print("Workout started : OK")

assert engine.is_running() is True

# ----------------------------------------------------------
# Empty pose
# ----------------------------------------------------------

landmarks = create_landmarks()

result = engine.process(landmarks)

print("Empty pose:", result)

assert result["exercise"] is None
assert result["status"] == "waiting"

print("Waiting state : OK")

# ----------------------------------------------------------
# Stop
# ----------------------------------------------------------

engine.stop()

assert engine.is_running() is False

print("Workout stopped : OK")

print("----------------------------")
print("Auto Workout Switching Test PASSED")