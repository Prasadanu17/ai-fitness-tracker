from ai_engine.analysis.angle_calculator import AngleCalculator


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


shoulder = Point(0, 0)
elbow = Point(1, 0)
wrist = Point(1, 1)


angle = AngleCalculator.calculate_angle(
    shoulder,
    elbow,
    wrist
)

print(f"Elbow angle: {angle:.2f} degrees")