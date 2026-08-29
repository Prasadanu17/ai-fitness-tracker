from ai_engine.exercises.base_analyzer import BaseExerciseAnalyzer


print("Base Exercise Analyzer Test")
print("---------------------------")


analyzer = BaseExerciseAnalyzer()


# --------------------------------------------------
# Test analyze() interface
# --------------------------------------------------

try:
    analyzer.analyze()
    raise AssertionError(
        "Base analyzer should not implement analyze()."
    )

except NotImplementedError:
    print("analyze() interface : OK")


# --------------------------------------------------
# Test get_result() interface
# --------------------------------------------------

try:
    analyzer.get_result()
    raise AssertionError(
        "Base analyzer should not implement get_result()."
    )

except NotImplementedError:
    print("get_result() interface : OK")


print("---------------------------")
print("Base Analyzer Test PASSED")