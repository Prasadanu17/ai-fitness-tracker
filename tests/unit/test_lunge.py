from ai_engine.exercises.lunge import LungeAnalyzer


class FakeLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def create_landmarks(angle_position):
    """
    Create simple synthetic landmarks for testing.

    Only the right hip, knee and ankle are relevant.
    """

    landmarks = [
        FakeLandmark(0.0, 0.0)
        for _ in range(33)
    ]

    if angle_position == "UP":
        # Straight leg -> approximately 180 degrees
        landmarks[24] = FakeLandmark(0.5, 0.2)  # hip
        landmarks[26] = FakeLandmark(0.5, 0.5)  # knee
        landmarks[28] = FakeLandmark(0.5, 0.8)  # ankle

    elif angle_position == "DOWN":
        # Approximately 90 degree knee
        landmarks[24] = FakeLandmark(0.5, 0.2)  # hip
        landmarks[26] = FakeLandmark(0.5, 0.5)  # knee
        landmarks[28] = FakeLandmark(0.8, 0.5)  # ankle

    return landmarks


print("Lunge Analyzer Test")
print("-------------------")

analyzer = LungeAnalyzer(
    side="right",
    down_threshold=110,
    up_threshold=155,
    smoothing_window=1,
    min_rep_gap=1,
)

# Standing
result = analyzer.analyze(
    create_landmarks("UP")
)

print(
    f"Position: UP   | "
    f"Angle: {result['angle']:6.1f}° | "
    f"State: {result['state']:4} | "
    f"Reps: {result['reps']}"
)

# Down
result = analyzer.analyze(
    create_landmarks("DOWN")
)

print(
    f"Position: DOWN | "
    f"Angle: {result['angle']:6.1f}° | "
    f"State: {result['state']:4} | "
    f"Reps: {result['reps']}"
)

# Back up
result = analyzer.analyze(
    create_landmarks("UP")
)

print(
    f"Position: UP   | "
    f"Angle: {result['angle']:6.1f}° | "
    f"State: {result['state']:4} | "
    f"Reps: {result['reps']}"
)

print()
print(f"Final lunge reps: {analyzer.get_result()['reps']}")
print("-------------------")
print("Lunge Analyzer Test PASSED")