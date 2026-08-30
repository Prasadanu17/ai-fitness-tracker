from ai_engine.registry.exercise_registry import (
    get_available_exercises,
    get_exercise_analyzer,
    is_exercise_supported,
)


print("Exercise Registry Test")
print("-----------------------")


# --------------------------------------------------
# Test 1: List available exercises
# --------------------------------------------------

exercises = get_available_exercises()

print(f"Available exercises: {exercises}")


# --------------------------------------------------
# Test 2: Check supported exercises
# --------------------------------------------------

assert is_exercise_supported("squat")
assert is_exercise_supported("bicep_curl")

print("Squat supported      : OK")
print("Bicep curl supported : OK")


# --------------------------------------------------
# Test 3: Create squat analyzer
# --------------------------------------------------

squat_analyzer = get_exercise_analyzer("squat", side="right")

print(f"Squat analyzer        : {type(squat_analyzer).__name__}")


# --------------------------------------------------
# Test 4: Create bicep curl analyzer
# --------------------------------------------------

bicep_analyzer = get_exercise_analyzer("bicep_curl", side="right")

print(f"Bicep curl analyzer   : {type(bicep_analyzer).__name__}")


# --------------------------------------------------
# Test 5: Unsupported exercise
# --------------------------------------------------

try:
    get_exercise_analyzer("deadlift")
    raise AssertionError("Unsupported exercise was accepted.")

except ValueError:
    print("Unsupported exercise : Correctly rejected")


print("-----------------------")
print("Exercise Registry Test PASSED")