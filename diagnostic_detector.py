"""
Diagnostic Detection Mode

Print detailed detection information for each frame.

Usage:
    python diagnostic_detector.py

Shows:
    - Raw detection candidates (squat, bicep_curl, lunge with confidence)
    - Stabilization state
    - Current confirmed exercise
    - Detection history
"""

import cv2
from ai_engine.pose_engine import PoseEngine
from ai_engine.detection.exercise_detector import ExerciseDetector


def make_diagnostic_detector():
    """Create a detector with detailed logging."""
    return ExerciseDetector()


def print_detection_header():
    print("\n" + "=" * 80)
    print("FRAME DETECTION DIAGNOSTIC")
    print("=" * 80)


def print_detection_result(frame_num, result, detector):
    """Print detailed detection information."""
    print(f"\n[FRAME {frame_num}]")

    # Raw detection
    exercise = result.get("exercise")
    confidence = result.get("confidence")
    side = result.get("side")

    print(f"  CONFIRMED EXERCISE: {exercise} (confidence={confidence}, side={side})")

    # Detector internals
    print(f"  DETECTOR STATE:")
    print(f"    Current:  {detector.current_exercise}")
    print(f"    Pending:  {detector.pending_exercise} (count={detector.pending_count})")
    print(f"    Confidence: {detector.current_confidence}")
    
    # Show pose angles - ALWAYS show to debug
    print(f"  ARM ANGLES:")
    if detector._last_arm_angles:
        for side_name, angle in detector._last_arm_angles:
            print(f"    {side_name}: {angle:.1f}°")
    else:
        print(f"    No valid arm angles")
    
    print(f"  LEG ANGLES:")
    if detector._last_leg_angles:
        right_angle, left_angle = detector._last_leg_angles
        if right_angle is not None:
            print(f"    Right knee: {right_angle:.1f}°")
        else:
            print(f"    Right knee: NOT VISIBLE")
        if left_angle is not None:
            print(f"    Left knee: {left_angle:.1f}°")
        else:
            print(f"    Left knee: NOT VISIBLE")
    else:
        print(f"    No valid leg angles")


def print_pose_validation(landmarks, detector):
    """Print the concrete reason a pose fails detector validation."""
    required_indexes = (
        detector.LEFT_SHOULDER,
        detector.RIGHT_SHOULDER,
        detector.LEFT_ELBOW,
        detector.RIGHT_ELBOW,
        detector.LEFT_WRIST,
        detector.RIGHT_WRIST,
        detector.LEFT_HIP,
        detector.RIGHT_HIP,
        detector.LEFT_KNEE,
        detector.RIGHT_KNEE,
        detector.LEFT_ANKLE,
        detector.RIGHT_ANKLE,
    )

    invalid = [
        index
        for index in required_indexes
        if not detector._is_valid_landmark(landmarks[index])
    ]
    if invalid:
        print(f"  INVALID REQUIRED LANDMARKS: {invalid}")

    short_pairs = []
    for index_a, index_b in (
        (detector.RIGHT_SHOULDER, detector.RIGHT_ELBOW),
        (detector.RIGHT_ELBOW, detector.RIGHT_WRIST),
        (detector.RIGHT_HIP, detector.RIGHT_KNEE),
        (detector.RIGHT_KNEE, detector.RIGHT_ANKLE),
        (detector.LEFT_SHOULDER, detector.LEFT_ELBOW),
        (detector.LEFT_ELBOW, detector.LEFT_WRIST),
        (detector.LEFT_HIP, detector.LEFT_KNEE),
        (detector.LEFT_KNEE, detector.LEFT_ANKLE),
    ):
        if detector._distance(landmarks[index_a], landmarks[index_b]) < 0.001:
            short_pairs.append((index_a, index_b))
    if short_pairs:
        print(f"  COLLAPSED BODY PAIRS: {short_pairs}")

    # History
    if detector.detection_history:
        history_str = " → ".join(
            str(e)[:8] for e in list(detector.detection_history)[-8:]
        )
        print(f"    History: {history_str}")


def main():
    print("=" * 80)
    print("AI GYM TRACKER - DETECTION DIAGNOSTIC MODE")
    print("=" * 80)
    print("\nThis tool prints detailed detection information for each frame.")
    print("Press 'q' to quit, 's' to pause/resume, 'r' to reset detector.\n")

    pose_engine = PoseEngine(
        model_path="models/pose_landmarker.task"
    )

    detector = make_diagnostic_detector()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Cannot open webcam")
        return

    frame_num = 0
    paused = False

    try:
        while True:
            ret, frame = camera.read()

            if not ret:
                print("ERROR: Cannot read frame")
                break

            frame_num += 1

            # Get key press (non-blocking)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("\nQuitting...")
                break

            if key == ord("s"):
                paused = not paused
                print(f"\n{'RESUMED' if not paused else 'PAUSED'}")
                continue

            if key == ord("r"):
                detector.reset()
                print("\nDETECTOR RESET")
                continue

            if paused:
                continue

            # Process frame
            try:
                pose_results = pose_engine.process_frame(frame)

                if pose_results is None:
                    continue

                landmarks = pose_engine.get_landmarks(pose_results)

                if landmarks is None or len(landmarks) < 33:
                    continue

                if not detector._has_valid_pose(landmarks):
                    if frame_num % 5 == 0:
                        print_pose_validation(landmarks, detector)

                # Detect
                result = detector.detect(landmarks)

                # Print diagnostic
                if frame_num % 5 == 0:  # Print every 5 frames to reduce spam
                    print_detection_header()
                    print_detection_result(frame_num, result, detector)

            except Exception as e:
                print(f"[ERROR Frame {frame_num}]: {e}")
                continue

            # Display frame
            cv2.imshow(
                "AI GYM Tracker - Diagnostic Mode (press 'q' to quit, 's' to pause, 'r' to reset)",
                frame,
            )

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("\nDiagnostic mode closed.")


if __name__ == "__main__":
    main()
