import cv2

from ai_engine.pose_engine import PoseEngine
from ai_engine.exercises.squat import SquatAnalyzer


def draw_text(frame, text, position, scale=0.7):
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main():

    pose_engine = PoseEngine()
    squat_analyzer = SquatAnalyzer(side="right")

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open webcam.")
        return

    print("===================================")
    print("AI GYM TRACKER - LIVE SQUAT TEST")
    print("===================================")
    print("Stand far enough away to show your")
    print("HEAD + HIP + KNEES + FEET.")
    print()
    print("Press Q to quit.")

    while True:

        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read webcam frame.")
            break

        results = pose_engine.process_frame(frame)

        if results.pose_landmarks:

            landmarks = results.pose_landmarks[0]

            result = squat_analyzer.analyze(landmarks)

            angle = result["angle"]
            reps = result["reps"]
            state = result["state"]
            form = result["form"]

            # --------------------------------
            # Header
            # --------------------------------

            draw_text(
                frame,
                "AI GYM TRACKER",
                (25, 40),
                1.0,
            )

            draw_text(
                frame,
                "EXERCISE: SQUAT",
                (25, 80),
                0.8,
            )

            # --------------------------------
            # Rep count
            # --------------------------------

            draw_text(
                frame,
                f"REPS: {reps}",
                (25, 130),
                0.9,
            )

            # --------------------------------
            # Angle
            # --------------------------------

            if angle is not None:

                draw_text(
                    frame,
                    f"KNEE ANGLE: {angle:.1f}",
                    (25, 170),
                    0.7,
                )

            # --------------------------------
            # State
            # --------------------------------

            draw_text(
                frame,
                f"STATE: {state}",
                (25, 210),
                0.7,
            )

            # --------------------------------
            # Form
            # --------------------------------

            draw_text(
                frame,
                f"FORM: {form}",
                (25, 250),
                0.7,
            )

        else:

            draw_text(
                frame,
                "NO POSE DETECTED",
                (25, 50),
                0.8,
            )

            draw_text(
                frame,
                "SHOW YOUR FULL BODY",
                (25, 90),
                0.7,
            )

        cv2.imshow(
            "AI GYM Tracker - Live Squat",
            frame,
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print()
    print("Live squat test stopped.")


if __name__ == "__main__":
    main()