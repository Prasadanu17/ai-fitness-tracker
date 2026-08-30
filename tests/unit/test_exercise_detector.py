"""
Exercise Detector Test
"""

from ai_engine.detection.exercise_detector import ExerciseDetector


def make_landmark(x, y, z=0.0, visibility=1.0):
    return type(
        "Landmark",
        (),
        {
            "x": x,
            "y": y,
            "z": z,
            "visibility": visibility,
        },
    )()


def create_empty_landmarks():
    return [
        make_landmark(0.0, 0.0)
        for _ in range(33)
    ]


def create_invisible_landmarks():
    return [
        make_landmark(
            0.5,
            0.5,
            visibility=0.0,
        )
        for _ in range(33)
    ]


print("Exercise Detector Test")
print("----------------------")


# ==========================================================
# CREATE DETECTOR
# ==========================================================

detector = ExerciseDetector()

print("Detector created : OK")


# ==========================================================
# EMPTY / INVALID POSE
# ==========================================================

landmarks = create_empty_landmarks()

result = detector.detect(landmarks)

print("Empty pose result:", result)

assert "exercise" in result
assert "confidence" in result
assert "side" in result

assert result["exercise"] is None
assert result["confidence"] == 0.0
assert result["side"] is None

print("Invalid pose     : OK")


# ==========================================================
# INVISIBLE POSE
# ==========================================================

landmarks = create_invisible_landmarks()

result = detector.detect(landmarks)

print("Invisible pose result:", result)

assert result["exercise"] is None
assert result["confidence"] == 0.0
assert result["side"] is None

print("Visibility check : OK")


# ==========================================================
# GETTERS
# ==========================================================

assert detector.get_current_exercise() is None
assert detector.get_confidence() == 0.0
assert detector.get_current_side() is None

print("Getters           : OK")


# ==========================================================
# RESET
# ==========================================================

detector.reset()

assert detector.get_current_exercise() is None
assert detector.get_confidence() == 0.0
assert detector.get_current_side() is None

print("Reset             : OK")


print("----------------------")
print("Exercise Detector Test PASSED")