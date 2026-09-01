"""
Debug angle calculations to verify pose geometry.
"""

import math
from ai_engine.analysis.angle_calculator import AngleCalculator


def make_landmark(x, y, z=0.0, visibility=0.9):
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


def create_squat_pose():
    landmarks = [make_landmark(0.5, 0.5) for _ in range(33)]

    # Right leg: create a VERY bent knee (angle ~115°)
    # Hip at (0.5, 0.35), Knee at (0.5, 0.65), Ankle at (0.70, 0.75)
    landmarks[24] = make_landmark(0.5, 0.35)
    landmarks[26] = make_landmark(0.5, 0.65)
    landmarks[28] = make_landmark(0.70, 0.75)

    # Left leg
    landmarks[23] = make_landmark(0.5, 0.35)
    landmarks[25] = make_landmark(0.5, 0.65)
    landmarks[27] = make_landmark(0.30, 0.75)

    # Shoulders
    landmarks[11] = make_landmark(0.45, 0.15)
    landmarks[12] = make_landmark(0.55, 0.15)

    # Elbows
    landmarks[13] = make_landmark(0.45, 0.35)
    landmarks[14] = make_landmark(0.55, 0.35)

    # Wrists
    landmarks[15] = make_landmark(0.45, 0.55)
    landmarks[16] = make_landmark(0.55, 0.55)

    return landmarks


def create_bicep_curl_pose():
    landmarks = [make_landmark(0.5, 0.5) for _ in range(33)]

    # Legs straight (nearly vertical)
    # Hip at (0.5, 0.35), Knee at (0.5, 0.65), Ankle at (0.51, 0.95)
    landmarks[24] = make_landmark(0.5, 0.35)
    landmarks[26] = make_landmark(0.5, 0.65)
    landmarks[28] = make_landmark(0.51, 0.95)

    landmarks[23] = make_landmark(0.5, 0.35)
    landmarks[25] = make_landmark(0.5, 0.65)
    landmarks[27] = make_landmark(0.49, 0.95)

    # Shoulders
    landmarks[11] = make_landmark(0.45, 0.15)
    landmarks[12] = make_landmark(0.55, 0.15)

    # Right arm BENT
    landmarks[14] = make_landmark(0.58, 0.35)
    landmarks[16] = make_landmark(0.50, 0.35)

    # Left arm STRAIGHT (vertical)
    landmarks[13] = make_landmark(0.45, 0.45)
    landmarks[15] = make_landmark(0.45, 0.75)

    return landmarks


# Test squat angles
print("SQUAT POSE ANGLES:")
print("-" * 60)
squat_pose = create_squat_pose()

right_hip = squat_pose[24]
right_knee = squat_pose[26]
right_ankle = squat_pose[28]

right_knee_angle = AngleCalculator.calculate_angle(
    right_hip, right_knee, right_ankle
)

print(
    f"Right knee angle (hip -> knee -> ankle): {right_knee_angle:.1f}°"
)
print(f"Expected: ~95-105° (bent knee)")

# Test bicep curl angles
print("\nBICEP CURL POSE ANGLES:")
print("-" * 60)
curl_pose = create_bicep_curl_pose()

# Right leg angle
right_hip = curl_pose[24]
right_knee = curl_pose[26]
right_ankle = curl_pose[28]

right_knee_angle = AngleCalculator.calculate_angle(
    right_hip, right_knee, right_ankle
)

print(
    f"Right knee angle (hip -> knee -> ankle): {right_knee_angle:.1f}°"
)
print(f"Expected: ~160-170° (straight leg)")

# Right arm angle (the curl)
right_shoulder = curl_pose[12]
right_elbow = curl_pose[14]
right_wrist = curl_pose[16]

right_elbow_angle = AngleCalculator.calculate_angle(
    right_shoulder, right_elbow, right_wrist
)

print(
    f"Right elbow angle (shoulder -> elbow -> wrist): {right_elbow_angle:.1f}°"
)
print(f"Expected: ~90-100° (bent arm in curl)")

# Left arm angle
left_shoulder = curl_pose[11]
left_elbow = curl_pose[13]
left_wrist = curl_pose[15]

left_elbow_angle = AngleCalculator.calculate_angle(
    left_shoulder, left_elbow, left_wrist
)

print(
    f"Left elbow angle (shoulder -> elbow -> wrist): {left_elbow_angle:.1f}°"
)
print(f"Expected: ~160-170° (straight arm)")

print("\nAdvantage (left - right):", left_elbow_angle - right_elbow_angle)
print(f"BICEP_SIDE_ADVANTAGE threshold: 20°")
