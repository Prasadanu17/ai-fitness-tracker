from ai_engine.exercise_selector import ExerciseSelector


print("Exercise Selector Test")
print("----------------------")


selector = ExerciseSelector()


# --------------------------------------------------
# Test 1: Available exercises
# --------------------------------------------------

exercises = selector.get_available_exercises()

print(f"Available exercises: {exercises}")

assert "squat" in exercises
assert "bicep_curl" in exercises


# --------------------------------------------------
# Test 2: Select squat
# --------------------------------------------------

analyzer = selector.select("squat", side="right")

print(f"Selected exercise  : {selector.get_current_exercise()}")
print(f"Analyzer           : {type(analyzer).__name__}")

assert selector.get_current_exercise() == "squat"
assert type(analyzer).__name__ == "SquatAnalyzer"


# --------------------------------------------------
# Test 3: Select bicep curl
# --------------------------------------------------

analyzer = selector.select("bicep_curl", side="right")

print(f"Selected exercise  : {selector.get_current_exercise()}")
print(f"Analyzer           : {type(analyzer).__name__}")

assert selector.get_current_exercise() == "bicep_curl"
assert type(analyzer).__name__ == "BicepCurlAnalyzer"


# --------------------------------------------------
# Test 4: Clear selection
# --------------------------------------------------

selector.clear()

print(f"After clear        : {selector.get_current_exercise()}")

assert selector.get_current_exercise() is None
assert selector.get_current_analyzer() is None


# --------------------------------------------------
# Test 5: Invalid exercise
# --------------------------------------------------

try:
    selector.select("deadlift")
    raise AssertionError("Unsupported exercise was accepted.")

except ValueError:
    print("Invalid exercise   : Correctly rejected")


print("----------------------")
print("Exercise Selector Test PASSED")