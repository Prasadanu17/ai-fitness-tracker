from ai_engine.exercises.squat import SquatAnalyzer


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def make_landmarks(position):
    """
    Create 33 test landmarks.

    right hip  = 24
    right knee = 26
    right ankle = 28
    """

    landmarks = [Point(0, 0) for _ in range(33)]

    if position == "UP":
        # Approximately straight leg
        landmarks[24] = Point(0, 0)
        landmarks[26] = Point(1, 0)
        landmarks[28] = Point(2, 0)

    elif position == "DOWN":
        # Approximately 90 degree knee angle
        landmarks[24] = Point(0, 0)
        landmarks[26] = Point(1, 0)
        landmarks[28] = Point(1, 1)

    return landmarks


analyzer = SquatAnalyzer(side="right")


sequence = [
    "UP",
    "UP",
    "DOWN",
    "DOWN",
    "DOWN",
    "UP",
    "UP",
]


print("Squat Complete Rep Test")
print("------------------------")

for position in sequence:

    landmarks = make_landmarks(position)

    result = analyzer.analyze(landmarks)

    print(
        f"Position: {position:<4} | "
        f"Angle: {result['angle']:>6.1f}° | "
        f"State: {result['state']:<4} | "
        f"Reps: {result['reps']}"
    )


print()
print(f"Final squat reps: {analyzer.get_result()['reps']}")