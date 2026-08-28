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

landmarks = make_landmarks()

# Simple 90-degree arm position
landmarks[12] = Point(0, 0)   # shoulder
landmarks[14] = Point(1, 0)   # elbow
landmarks[16] = Point(1, 1)   # wrist

result = analyzer.analyze(landmarks)

print("Bicep Curl Analyzer Test")
print("-------------------------")
print(f"Exercise : {result['exercise']}")
print(f"Side     : {result['side']}")
print(f"Angle    : {result['angle']}°")
print(f"Reps     : {result['reps']}")
print(f"State    : {result['state']}")
print(f"Form     : {result['form']}")