from ai_engine.exercises.bicep_curl import BicepCurlAnalyzer


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_landmarks():
    """
    Create 33 fake landmarks.

    We only need:
        12 = right shoulder
        14 = right elbow
        16 = right wrist
    """

    landmarks = [
        Point(0, 0)
        for _ in range(33)
    ]

    return landmarks


analyzer = BicepCurlAnalyzer(side="right")

base_landmarks = make_landmarks()
base_landmarks[12] = Point(0, 0)   # shoulder
base_landmarks[14] = Point(1, 0)   # elbow
base_landmarks[16] = Point(2, 0)   # wrist

bent_landmarks = make_landmarks()
bent_landmarks[12] = Point(0, 0)   # shoulder
bent_landmarks[14] = Point(1, 0)   # elbow
bent_landmarks[16] = Point(1, 1)   # wrist

# Realistic extended -> curl -> extended sequence.
for _ in range(3):
    analyzer.analyze(base_landmarks)
for _ in range(6):
    analyzer.analyze(bent_landmarks)
for _ in range(4):
    analyzer.analyze(base_landmarks)

result = analyzer.get_result()
assert result["reps"] == 1, result
assert result["side"] == "right", result

print("Bicep Curl Analyzer Test")
print("-------------------------")
print(f"Exercise : {result['exercise']}")
print(f"Side     : {result['side']}")
print(f"Angle    : {result['angle']}°")
print(f"Reps     : {result['reps']}")
print(f"State    : {result['state']}")
print(f"Form     : {result['form']}")