"""
Live Automatic Workout Test
"""

from ai_engine.workout.live_auto_workout import LiveAutoWorkout


print("Live Automatic Workout Test")
print("----------------------------")


# ==========================================================
# CREATE
# ==========================================================

workout = LiveAutoWorkout()

print(
    "Engine created : OK"
)


# ==========================================================
# INITIAL STATE
# ==========================================================

assert workout.running is False

print(
    "Initial state   : OK"
)


# ==========================================================
# WAITING RESULT
# ==========================================================

result = workout.process_frame(None)

assert isinstance(result, dict)
assert result["exercise"] is None
assert result["status"] == "waiting"

print(
    "Waiting result  : OK"
)


# ==========================================================
# RESULT ACCESS
# ==========================================================

current = workout.get_result()

assert isinstance(current, dict)
assert current["status"] == "waiting"

print(
    "Result access   : OK"
)


# ==========================================================
# RESET
# ==========================================================

workout.reset()

print(
    "Reset           : OK"
)


# ==========================================================
# CLOSE
# ==========================================================

workout.close()

print(
    "Resources close : OK"
)


print("----------------------------")
print("Live Automatic Workout Test PASSED")