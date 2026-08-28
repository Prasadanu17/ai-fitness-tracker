import cv2

from ai_engine.pose_engine import PoseEngine


# MediaPipe Pose landmark connections
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),

    (9, 10),

    (11, 12),

    (11, 13), (13, 15),
    (15, 17), (15, 19), (15, 21),

    (12, 14), (14, 16),
    (16, 18), (16, 20), (16, 22),

    (11, 23),
    (12, 24),

    (23, 24),

    (23, 25), (25, 27),
    (27, 29), (29, 31),

    (24, 26), (26, 28),
    (28, 30), (30, 32),
]


def draw_pose(frame, landmarks):
    height, width, _ = frame.shape

    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        points.append((x, y))

        cv2.circle(
            frame,
            (x, y),
            5,
            (0, 255, 0),
            -1
        )

    for start, end in POSE_CONNECTIONS:
        if start < len(points) and end < len(points):
            cv2.line(
                frame,
                points[start],
                points[end],
                (255, 0, 0),
                2
            )


def main():
    pose_engine = PoseEngine()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open webcam.")
        return

    print("Webcam started.")
    print("Pose detection active.")
    print("Press Q in the camera window to quit.")

    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read frame.")
            break

        results = pose_engine.process_frame(frame)

        landmarks = pose_engine.get_landmarks(results)

        if landmarks:
            draw_pose(frame, landmarks)

        cv2.imshow(
            "AI Gym Tracker - Pose Test",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    pose_engine.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()