"""
Automatic Movement Simulation Test

Simulates realistic landmark geometry for:

    Squat
    Bicep Curl
    Lunge

Pipeline under test:

    Synthetic Landmarks
            ↓
    ExerciseDetector
            ↓
    DetectionStabilizer
            ↓
    AutoWorkoutEngine
            ↓
    ExerciseSelector
            ↓
    Exercise Analyzer
"""


from ai_engine.workout.auto_workout_engine import AutoWorkoutEngine


# ==========================================================
# LANDMARK HELPER
# ==========================================================

def make_landmark(x, y, z=0.0):
    return type(
        "Landmark",
        (),
        {
            "x": float(x),
            "y": float(y),
            "z": float(z),
            "visibility": 1.0,
        },
    )()


# ==========================================================
# BASE POSE
# ==========================================================

def create_pose():
    """
    Create 33 MediaPipe-compatible landmarks.

    The coordinates are normalized approximately to
    a standing human pose.
    """

    landmarks = [
        make_landmark(0.0, 0.0)
        for _ in range(33)
    ]

    # ------------------------------------------------------
    # Shoulders
    # ------------------------------------------------------

    landmarks[11] = make_landmark(0.40, 0.30)  # left
    landmarks[12] = make_landmark(0.60, 0.30)  # right

    # ------------------------------------------------------
    # Elbows
    # ------------------------------------------------------

    landmarks[13] = make_landmark(0.35, 0.45)  # left
    landmarks[14] = make_landmark(0.65, 0.45)  # right

    # ------------------------------------------------------
    # Wrists
    # ------------------------------------------------------

    landmarks[15] = make_landmark(0.30, 0.60)  # left
    landmarks[16] = make_landmark(0.70, 0.60)  # right

    # ------------------------------------------------------
    # Hips
    # ------------------------------------------------------

    landmarks[23] = make_landmark(0.43, 0.55)  # left
    landmarks[24] = make_landmark(0.57, 0.55)  # right

    # ------------------------------------------------------
    # Knees
    # ------------------------------------------------------

    landmarks[25] = make_landmark(0.43, 0.75)  # left
    landmarks[26] = make_landmark(0.57, 0.75)  # right

    # ------------------------------------------------------
    # Ankles
    # ------------------------------------------------------

    landmarks[27] = make_landmark(0.43, 0.95)  # left
    landmarks[28] = make_landmark(0.57, 0.95)  # right

    return landmarks


# ==========================================================
# SQUAT POSE
# ==========================================================

def create_squat_pose():
    """
    Both knees approximately 90 degrees.

    This should be detected as squat.
    """

    landmarks = create_pose()

    # Left leg
    landmarks[23] = make_landmark(0.43, 0.50)
    landmarks[25] = make_landmark(0.43, 0.70)
    landmarks[27] = make_landmark(0.63, 0.70)

    # Right leg
    landmarks[24] = make_landmark(0.57, 0.50)
    landmarks[26] = make_landmark(0.57, 0.70)
    landmarks[28] = make_landmark(0.37, 0.70)

    return landmarks


# ==========================================================
# BICEP CURL POSE
# ==========================================================

def create_bicep_curl_pose():
    """
    Right elbow approximately 90 degrees.

    This should be detected as bicep curl.
    """

    landmarks = create_pose()

    # Right arm:
    #
    # shoulder
    #     |
    #     |
    #   elbow ---- wrist

    landmarks[12] = make_landmark(0.60, 0.30)
    landmarks[14] = make_landmark(0.60, 0.45)
    landmarks[16] = make_landmark(0.75, 0.45)

    return landmarks


# ==========================================================
# LUNGE POSE
# ==========================================================

def create_lunge_pose():
    """
    Right knee bent.
    Left knee extended.

    This should be detected as lunge.
    """

    landmarks = create_pose()

    # Right leg bent approximately 90 degrees.

    landmarks[24] = make_landmark(0.57, 0.50)
    landmarks[26] = make_landmark(0.57, 0.70)
    landmarks[28] = make_landmark(0.77, 0.70)

    # Left leg remains extended.

    landmarks[23] = make_landmark(0.43, 0.50)
    landmarks[25] = make_landmark(0.43, 0.72)
    landmarks[27] = make_landmark(0.43, 0.95)

    return landmarks


# ==========================================================
# TEST HELPERS
# ==========================================================

def feed_frames(engine, landmarks, count=3):
    """
    Feed the same pose for several consecutive frames.
    """

    results = []

    for _ in range(count):
        result = engine.process(landmarks)
        results.append(result)

    return results


# ==========================================================
# TEST
# ==========================================================

print("Automatic Movement Simulation Test")
print("-----------------------------------")


engine = AutoWorkoutEngine(
    confirmation_frames=3,
    minimum_confidence=0.60,
)

print("Engine created : OK")

engine.start()

print("Workout started : OK")


# ==========================================================
# SQUAT
# ==========================================================

print()
print("Testing SQUAT...")

squat_pose = create_squat_pose()

squat_results = feed_frames(
    engine,
    squat_pose,
    count=3,
)

for index, result in enumerate(squat_results, start=1):
    print(
        f"Frame {index}: "
        f"Detected={result['detected_exercise']} | "
        f"Exercise={result['exercise']} | "
        f"Status={result['status']}"
    )

assert squat_results[-1]["exercise"] == "squat"

assert (
    engine.get_current_analyzer().__class__.__name__
    == "SquatAnalyzer"
)

print("Squat automatic detection : OK")
print("Squat analyzer selection  : OK")


# ==========================================================
# BICEP CURL
# ==========================================================

print()
print("Testing BICEP CURL...")

bicep_pose = create_bicep_curl_pose()

bicep_results = feed_frames(
    engine,
    bicep_pose,
    count=3,
)

for index, result in enumerate(bicep_results, start=1):
    print(
        f"Frame {index}: "
        f"Detected={result['detected_exercise']} | "
        f"Exercise={result['exercise']} | "
        f"Status={result['status']}"
    )

assert bicep_results[-1]["exercise"] == "bicep_curl"

assert (
    engine.get_current_analyzer().__class__.__name__
    == "BicepCurlAnalyzer"
)

print("Bicep curl detection : OK")
print("Bicep analyzer switch : OK")


# ==========================================================
# LUNGE
# ==========================================================

print()
print("Testing LUNGE...")

lunge_pose = create_lunge_pose()

lunge_results = feed_frames(
    engine,
    lunge_pose,
    count=3,
)

for index, result in enumerate(lunge_results, start=1):
    print(
        f"Frame {index}: "
        f"Detected={result['detected_exercise']} | "
        f"Exercise={result['exercise']} | "
        f"Status={result['status']}"
    )

assert lunge_results[-1]["exercise"] == "lunge"

assert (
    engine.get_current_analyzer().__class__.__name__
    == "LungeAnalyzer"
)

print("Lunge automatic detection : OK")
print("Lunge analyzer switch    : OK")


# ==========================================================
# CLEANUP
# ==========================================================

engine.stop()

assert engine.is_running() is False

print()
print("Workout stopped : OK")

print("-----------------------------------")
print("Automatic Movement Simulation Test PASSED")