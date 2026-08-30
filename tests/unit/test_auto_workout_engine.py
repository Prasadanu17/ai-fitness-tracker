"""
Auto Workout Engine Test
"""

from ai_engine.workout.auto_workout_engine import AutoWorkoutEngine


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


def create_empty_landmarks():
    return [
        make_landmark(0.0, 0.0)
        for _ in range(33)
    ]


print("Auto Workout Engine Test")
print("------------------------")

engine = AutoWorkoutEngine()

print("Engine created : OK")

assert engine.is_running() is False

engine.start()

assert engine.is_running() is True

print("Workout started : OK")

available = engine.get_available_exercises()

print("Available exercises:", available)

assert "squat" in available
assert "bicep_curl" in available
assert "lunge" in available

print("Exercise registry : OK")

# ----------------------------------------------------------
# Empty / invalid pose
# ----------------------------------------------------------

landmarks = create_empty_landmarks()

result = engine.process(landmarks)

print("Empty pose result:", result)

assert result["status"] == "waiting"
assert result["detected_exercise"] is None
assert engine.get_current_exercise() is None

print("Invalid pose handling : OK")

# ----------------------------------------------------------
# Reset
# ----------------------------------------------------------

engine.reset()

print("Reset : OK")

# ----------------------------------------------------------
# Stop
# ----------------------------------------------------------

engine.stop()

assert engine.is_running() is False
assert engine.get_current_exercise() is None
assert engine.get_current_analyzer() is None

print("Workout stopped : OK")

print("------------------------")
print("Auto Workout Engine Test PASSED")