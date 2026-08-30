"""
AI Fitness Tracker - Live Webcam Application

Pipeline:

    Webcam
       ↓
    PoseEngine
       ↓
    LiveWorkout
       ↓
    WorkoutEngine
       ↓
    Exercise Analyzer
       ↓
    Live result

Controls:

    Q = Quit
    R = Reset reps
    1 = Squat
    2 = Bicep Curl
    3 = Lunge
"""

import cv2

from ai_engine.workout.live_workout import LiveWorkout


# ==========================================================
# CONFIGURATION
# ==========================================================

WINDOW_NAME = "AI Fitness Tracker"

EXERCISES = {
    ord("1"): ("squat", "Squat"),
    ord("2"): ("bicep_curl", "Bicep Curl"),
    ord("3"): ("lunge", "Lunge"),
}


# ==========================================================
# UI HELPERS
# ==========================================================

def draw_text(
    frame,
    text,
    position,
    scale=0.7,
    thickness=2,
):
    """
    Draw readable text on the webcam frame.
    """

    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def draw_dashboard(frame, result, exercise_name):
    """
    Draw workout information over the webcam feed.
    """

    height, width = frame.shape[:2]

    # ------------------------------------------------------
    # Dashboard background
    # ------------------------------------------------------

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (20, 20),
        (390, 275),
        (0, 0, 0),
        -1,
    )

    # Slight transparency
    cv2.addWeighted(
        overlay,
        0.65,
        frame,
        0.35,
        0,
        frame,
    )

    # ------------------------------------------------------
    # Title
    # ------------------------------------------------------

    draw_text(
        frame,
        "AI FITNESS TRACKER",
        (40, 55),
        scale=0.8,
        thickness=2,
    )

    # ------------------------------------------------------
    # Exercise
    # ------------------------------------------------------

    draw_text(
        frame,
        f"Exercise: {exercise_name}",
        (40, 90),
    )

    # ------------------------------------------------------
    # Detection
    # ------------------------------------------------------

    detected = result.get("detected", False)

    if not detected:
        draw_text(
            frame,
            "Status: NO POSE",
            (40, 125),
        )

        draw_text(
            frame,
            result.get(
                "form",
                "Move into camera view",
            ),
            (40, 160),
            scale=0.6,
        )

        draw_text(
            frame,
            "Reps: 0",
            (40, 205),
        )

        draw_text(
            frame,
            "Angle: --",
            (40, 240),
        )

        return

    # ------------------------------------------------------
    # Analysis
    # ------------------------------------------------------

    reps = result.get("reps", 0)

    angle = result.get("angle")

    state = result.get(
        "state",
        "UNKNOWN",
    )

    form = result.get(
        "form",
        "Unknown",
    )

    # ------------------------------------------------------
    # Display values
    # ------------------------------------------------------

    draw_text(
        frame,
        f"Reps: {reps}",
        (40, 130),
    )

    if angle is None:
        angle_text = "Angle: --"
    else:
        angle_text = f"Angle: {angle:.1f} deg"

    draw_text(
        frame,
        angle_text,
        (40, 170),
    )

    draw_text(
        frame,
        f"State: {state}",
        (40, 210),
    )

    draw_text(
        frame,
        f"Form: {form}",
        (40, 250),
        scale=0.55,
    )


def draw_controls(frame):
    """
    Draw keyboard controls at the bottom.
    """

    height = frame.shape[0]

    text = (
        "1: Squat   "
        "2: Bicep Curl   "
        "3: Lunge   "
        "R: Reset   "
        "Q: Quit"
    )

    draw_text(
        frame,
        text,
        (25, height - 25),
        scale=0.55,
        thickness=1,
    )


# ==========================================================
# MAIN APPLICATION
# ==========================================================

def main():

    print("=" * 50)
    print("AI FITNESS TRACKER")
    print("=" * 50)
    print()
    print("1 - Squat")
    print("2 - Bicep Curl")
    print("3 - Lunge")
    print()
    print("Press Q to quit.")
    print("Press R to reset reps.")
    print()

    # ------------------------------------------------------
    # Create live workout
    # ------------------------------------------------------

    live_workout = LiveWorkout()

    # ------------------------------------------------------
    # Open webcam
    # ------------------------------------------------------

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("ERROR: Could not open webcam.")

        live_workout.close()

        return

    # ------------------------------------------------------
    # Default exercise
    # ------------------------------------------------------

    current_exercise = "squat"
    current_display_name = "Squat"

    live_workout.start(
        current_exercise,
        side="right",
    )

    print(
        f"Starting exercise: {current_display_name}"
    )

    # ------------------------------------------------------
    # Main loop
    # ------------------------------------------------------

    try:

        while True:

            success, frame = camera.read()

            if not success:

                print(
                    "WARNING: Could not read webcam frame."
                )

                break

            # ------------------------------------------------
            # Mirror webcam
            # ------------------------------------------------

            frame = cv2.flip(
                frame,
                1,
            )

            # ------------------------------------------------
            # Process frame
            # ------------------------------------------------

            result = live_workout.process_frame(
                frame
            )

            # ------------------------------------------------
            # Draw dashboard
            # ------------------------------------------------

            draw_dashboard(
                frame,
                result,
                current_display_name,
            )

            draw_controls(frame)

            # ------------------------------------------------
            # Show frame
            # ------------------------------------------------

            cv2.imshow(
                WINDOW_NAME,
                frame,
            )

            # ------------------------------------------------
            # Keyboard
            # ------------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            # Q = quit
            if key == ord("q"):

                break

            # R = reset
            elif key == ord("r"):

                live_workout.reset()

                print(
                    f"{current_display_name} reps reset."
                )

            # Exercise selection
            elif key in EXERCISES:

                exercise_name, display_name = (
                    EXERCISES[key]
                )

                current_exercise = exercise_name
                current_display_name = display_name

                live_workout.stop()

                live_workout.start(
                    current_exercise,
                    side="right",
                )

                print(
                    f"Switched to: "
                    f"{current_display_name}"
                )

    finally:

        # ------------------------------------------------------
        # Cleanup
        # ------------------------------------------------------

        camera.release()

        cv2.destroyAllWindows()

        live_workout.close()

        print()
        print("AI Fitness Tracker stopped.")


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    main()