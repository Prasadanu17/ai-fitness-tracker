"""
Squat Form Analyzer Test
"""

from ai_engine.form.squat_form import SquatFormAnalyzer


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


print("Squat Form Analyzer Test")
print("------------------------")

analyzer = SquatFormAnalyzer()

print("Analyzer created : OK")

landmarks = create_landmarks()

result = analyzer.analyze(landmarks)

print("Result:", result)

assert "exercise" in result
assert "score" in result
assert "status" in result
assert "feedback" in result
assert "knee_angle" in result

print("Result structure : OK")

analyzer.reset()

reset_result = analyzer.get_result()

assert reset_result["score"] == 0.0
assert reset_result["status"] == "Waiting"

print("Reset            : OK")

print("------------------------")
print("Squat Form Analyzer Test PASSED")