import cv2

from ai_engine.pose_engine import PoseEngine
from ai_engine.analysis.angle_calculator import AngleCalculator


# MediaPipe landmark indexes
RIGHT_SHOULDER = 12
RIGHT_ELBOW = 14
RIGHT_WRIST = 16


def main():
    pose_engine = PoseEngine()
    angle_calculator = AngleCalculator()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open webcam.")
        return

    print("Live angle test started.")
    print("Press Q to quit.")

    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read frame.")
            break

        results = pose_engine.process_frame(frame)
        landmarks = pose_engine.get_landmarks(results)

        if landmarks:
            shoulder = landmarks[RIGHT_SHOULDER]
            elbow = landmarks[RIGHT_ELBOW]
            wrist = landmarks[RIGHT_WRIST]

            angle = angle_calculator.calculate_angle(
                shoulder,
                elbow,
                wrist
            )

            cv2.putText(
                frame,
                f"Right Elbow: {angle:.1f} deg",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        cv2.imshow(
            "AI Gym Tracker - Live Angle",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    pose_engine.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()