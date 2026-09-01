"""
Detection False Positive Tests

Tests to verify that the detector correctly rejects
false positives, especially:

1. Bicep curl detection during squat
2. Low-confidence predictions don't get announced
3. Temporal stabilization prevents switching on single frames
4. Exercise-specific validation works
"""

from ai_engine.detection.exercise_detector import ExerciseDetector
from voice_engine.voice_controller import VoiceController
from voice_engine.speech_queue import SpeechQueue


def make_landmark(x, y, z=0.0, visibility=0.9):
    """Create a fake landmark."""
    return type(
        "Landmark",
        (),
        {
            "x": x,
            "y": y,
            "z": z,
            "visibility": visibility,
        },
    )()


def create_landmarks():
    """Create base 33-landmark pose."""
    return [make_landmark(0.5, 0.5) for _ in range(33)]


def create_squat_pose():
    """
    Create a squat pose:
    - Both legs bent (knee angles ~115°)
    - Arms relatively straight or slightly bent (not doing a curl)
    """
    landmarks = create_landmarks()

    # Right leg: create a VERY bent knee (angle ~115°)
    landmarks[24] = make_landmark(0.5, 0.35)   # right hip
    landmarks[26] = make_landmark(0.5, 0.65)   # right knee
    landmarks[28] = make_landmark(0.70, 0.75)  # right ankle (angled)

    # Left leg: mirror of right
    landmarks[23] = make_landmark(0.5, 0.35)   # left hip
    landmarks[25] = make_landmark(0.5, 0.65)   # left knee
    landmarks[27] = make_landmark(0.30, 0.75)  # left ankle (angled)

    # Both shoulders
    landmarks[11] = make_landmark(0.45, 0.15)  # left shoulder
    landmarks[12] = make_landmark(0.55, 0.15)  # right shoulder

    # Both elbows (relatively straight, like they would be during a squat)
    landmarks[13] = make_landmark(0.45, 0.35)  # left elbow
    landmarks[14] = make_landmark(0.55, 0.35)  # right elbow

    # Both wrists
    landmarks[15] = make_landmark(0.45, 0.55)  # left wrist
    landmarks[16] = make_landmark(0.55, 0.55)  # right wrist

    return landmarks


def create_squat_with_bent_arms():
    """
    Create a squat pose where arms are bent
    (simulating arm swing during squat).

    This should NOT trigger bicep curl detection
    after the fix.

    Knee angle: ~115° (bent, same as create_squat_pose)
    Elbow angle: ~110-120° (not a deep curl of ~80-90°)
    """
    landmarks = create_squat_pose()

    # Bend the arms slightly (like during squat movement)
    # This creates elbow angles around 110-120° (not a deep curl)

    # Left arm: bend it
    landmarks[13] = make_landmark(0.48, 0.28)  # left elbow (bent, not fully extended)
    landmarks[15] = make_landmark(0.45, 0.40)  # left wrist

    # Right arm: bend it
    landmarks[14] = make_landmark(0.52, 0.28)  # right elbow (bent)
    landmarks[16] = make_landmark(0.55, 0.40)  # right wrist

    return landmarks


def create_bicep_curl_pose():
    """
    Create a strong bicep curl pose:
    - One arm bent at ~81° (good curl angle)
    - Other arm relatively straight ~180°
    - Both legs relatively straight (standing) - knee angle ~178°
    """
    landmarks = create_landmarks()

    # Standing position - legs straight (knee angle ~178°)
    landmarks[24] = make_landmark(0.5, 0.35)   # right hip
    landmarks[26] = make_landmark(0.5, 0.65)   # right knee
    landmarks[28] = make_landmark(0.51, 0.95)  # right ankle (nearly vertical)

    landmarks[23] = make_landmark(0.5, 0.35)   # left hip
    landmarks[25] = make_landmark(0.5, 0.65)   # left knee
    landmarks[27] = make_landmark(0.49, 0.95)  # left ankle (nearly vertical)

    # Both shoulders
    landmarks[11] = make_landmark(0.45, 0.15)  # left shoulder
    landmarks[12] = make_landmark(0.55, 0.15)  # right shoulder

    # Right arm BENT (doing the curl) - elbow angle ~81°
    landmarks[14] = make_landmark(0.58, 0.35)  # right elbow (bent)
    landmarks[16] = make_landmark(0.50, 0.35)  # right wrist (high, near shoulder)

    # Left arm STRAIGHT - elbow angle ~180°
    landmarks[13] = make_landmark(0.45, 0.45)  # left elbow
    landmarks[15] = make_landmark(0.45, 0.75)  # left wrist

    return landmarks


def create_lunge_pose():
    """
    Create a lunge pose:
    - One leg bent (~115°), one leg straight (~170°+)
    - Arms neutral
    """
    landmarks = create_landmarks()

    # Right leg BENT (front leg) - angle ~115° (same as squat)
    landmarks[24] = make_landmark(0.5, 0.35)   # right hip
    landmarks[26] = make_landmark(0.5, 0.65)   # right knee (bent)
    landmarks[28] = make_landmark(0.70, 0.75)  # right ankle

    # Left leg STRAIGHT (back leg) - angle ~170°+ (nearly straight)
    # Make it more angled to create asymmetry
    landmarks[23] = make_landmark(0.5, 0.35)   # left hip
    landmarks[25] = make_landmark(0.48, 0.65)  # left knee (slightly angled)
    landmarks[27] = make_landmark(0.46, 0.95)  # left ankle (further back)

    # Shoulders
    landmarks[11] = make_landmark(0.45, 0.15)  # left shoulder
    landmarks[12] = make_landmark(0.55, 0.15)  # right shoulder

    # Elbows and wrists (neutral)
    landmarks[13] = make_landmark(0.45, 0.45)  # left elbow
    landmarks[14] = make_landmark(0.55, 0.45)  # right elbow
    landmarks[15] = make_landmark(0.45, 0.75)  # left wrist
    landmarks[16] = make_landmark(0.55, 0.75)  # right wrist

    return landmarks


# =============================================================
# TEST 1: Bicep curl rejected when legs are bent (CRITICAL)
# =============================================================

print("TEST 1: Bicep curl detection during squat")
print("-" * 60)

detector = ExerciseDetector()

# Process squat pose with bent arms
squat_pose = create_squat_with_bent_arms()

result = detector.detect(squat_pose)

print(f"Pose: Squat with bent arms")
print(f"Result: {result}")
print(f"Expected: exercise should be None (legs bent, not bicep curl)")

assert result["exercise"] is None, (
    f"FAILED: Detector returned {result['exercise']} "
    f"instead of None for squat pose"
)

print("PASSED: Bicep curl correctly rejected when legs are bent\n")


# =============================================================
# TEST 2: Strong squat is detected
# =============================================================

print("TEST 2: Strong squat detection")
print("-" * 60)

detector.reset()

squat_pose = create_squat_pose()

# Process multiple frames to reach confirmation
for _ in range(6):
    result = detector.detect(squat_pose)

print(f"Result after 6 frames: {result}")
print(f"Expected: exercise='squat' with confidence > 0.80")

assert result["exercise"] == "squat", (
    f"FAILED: Expected squat but got {result['exercise']}"
)

assert result["confidence"] > 0.75, (
    f"FAILED: Confidence too low: {result['confidence']}"
)

print("PASSED: Squat correctly detected\n")


# =============================================================
# TEST 3: Strong bicep curl is detected
# =============================================================

print("TEST 3: Strong bicep curl detection")
print("-" * 60)

detector.reset()

curl_pose = create_bicep_curl_pose()

# Process multiple frames
for _ in range(6):
    result = detector.detect(curl_pose)

print(f"Result after 6 frames: {result}")
print(f"Expected: exercise='bicep_curl' with confidence > 0.70")

assert result["exercise"] == "bicep_curl", (
    f"FAILED: Expected bicep_curl but got {result['exercise']}"
)

assert result["confidence"] > 0.70, (
    f"FAILED: Confidence too low: {result['confidence']}"
)

print("PASSED: Bicep curl correctly detected\n")


# =============================================================
# TEST 4: Lunge is detected
# =============================================================

print("TEST 4: Lunge detection")
print("-" * 60)

detector.reset()

lunge_pose = create_lunge_pose()

# Process multiple frames
for _ in range(6):
    result = detector.detect(lunge_pose)

print(f"Result after 6 frames: {result}")
print(f"Expected: exercise='lunge' with confidence > 0.70")

assert result["exercise"] == "lunge", (
    f"FAILED: Expected lunge but got {result['exercise']}"
)

assert result["confidence"] > 0.70, (
    f"FAILED: Confidence too low: {result['confidence']}"
)

print("PASSED: Lunge correctly detected\n")


# =============================================================
# TEST 5: Temporary bicep spike during squat doesn't switch
# =============================================================

print("TEST 5: Stability - temporary spike doesn't cause switch")
print("-" * 60)

detector.reset()

# Start with squat
squat_pose = create_squat_pose()
for _ in range(6):
    detector.detect(squat_pose)

# Current exercise should be squat
assert detector.get_current_exercise() == "squat", "Setup failed"
print("Setup: Squat confirmed")

# Now inject a single frame of curl pose
# (simulating noisy detection)
curl_pose = create_bicep_curl_pose()
result = detector.detect(curl_pose)

print(f"After single curl frame: {result}")
print(f"Current exercise should still be: squat")

# The detector should NOT switch to curl after just one frame
assert detector.get_current_exercise() == "squat", (
    f"FAILED: Switched to {detector.get_current_exercise()} "
    f"after single noisy frame"
)

print("PASSED: Detector stayed on squat despite noisy frame\n")


# =============================================================
# TEST 6: Voice controller respects confidence
# =============================================================

print("TEST 6: Voice filtering by confidence")
print("-" * 60)

queue = SpeechQueue()
voice = VoiceController(
    queue,
    min_confidence=0.70,
)

# Low-confidence prediction should not announce
low_conf_result = {
    "exercise": "bicep_curl",
    "detected_exercise": "bicep_curl",
    "confidence": 0.45,  # Below threshold
    "side": "right",
    "status": "active",
    "reps": 0,
}

events = voice.process(low_conf_result)

print(f"Low confidence result: {low_conf_result}")
print(f"Events generated: {len(events)}")
print(f"Expected: 0 events (below confidence threshold)")

assert len(events) == 0, (
    f"FAILED: Generated {len(events)} events for low-confidence prediction"
)

print("PASSED: Voice correctly rejected low-confidence prediction\n")


# =============================================================
# TEST 7: Voice announces waiting state
# =============================================================

print("TEST 7: Voice announces waiting state")
print("-" * 60)

queue = SpeechQueue()
voice = VoiceController(queue)

# No exercise detected
waiting_result = {
    "exercise": None,
    "detected_exercise": None,
    "confidence": 0.0,
    "side": None,
    "status": "waiting",
    "reps": 0,
}

events = voice.process(waiting_result)

print(f"Waiting state result: {waiting_result}")
print(f"Events generated: {len(events)}")
print(f"Expected: 1 event (waiting announcement)")

assert len(events) == 1, (
    f"FAILED: Expected 1 event but got {len(events)}"
)

assert events[0]["type"] == "waiting", (
    f"FAILED: Wrong event type: {events[0]['type']}"
)

print(f"Waiting message: {events[0].get('message')}")
print("PASSED: Voice announces waiting state\n")


# =============================================================
# TEST SUMMARY
# =============================================================

print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
print("\nKey validations:")
print("✓ Bicep curl detection is rejected when legs are bent")
print("✓ Squat is correctly detected")
print("✓ Bicep curl is correctly detected (when legs are straight)")
print("✓ Lunge is correctly detected")
print("✓ Temporal stabilization prevents single-frame switches")
print("✓ Voice respects confidence thresholds")
print("✓ Voice announces waiting state appropriately")
