"""
Detection Stabilizer Test
"""

from ai_engine.detection_stabilizer import DetectionStabilizer


print("Detection Stabilizer Test")
print("-------------------------")

# ----------------------------------------------------------
# Create
# ----------------------------------------------------------

stabilizer = DetectionStabilizer(
    confirmation_frames=3,
    minimum_confidence=0.60,
)

print("Stabilizer created : OK")

assert stabilizer.get_current_exercise() is None
assert stabilizer.is_confirmed() is False

# ----------------------------------------------------------
# Frame 1
# ----------------------------------------------------------

result = stabilizer.update(
    "squat",
    0.90,
    "right",
)

print("Frame 1:", result)

assert result["status"] == "detecting"
assert result["candidate_frames"] == 1
assert stabilizer.get_current_exercise() is None

# ----------------------------------------------------------
# Frame 2
# ----------------------------------------------------------

result = stabilizer.update(
    "squat",
    0.92,
    "right",
)

print("Frame 2:", result)

assert result["status"] == "detecting"
assert result["candidate_frames"] == 2

# ----------------------------------------------------------
# Frame 3
# ----------------------------------------------------------

result = stabilizer.update(
    "squat",
    0.91,
    "right",
)

print("Frame 3:", result)

assert result["status"] == "confirmed"
assert result["exercise"] == "squat"
assert result["side"] == "right"

print("Squat confirmation : OK")

# ----------------------------------------------------------
# Noise frame
# ----------------------------------------------------------

result = stabilizer.update(
    "bicep_curl",
    0.95,
    "right",
)

print("Noise frame:", result)

assert result["exercise"] == "squat"
assert result["status"] == "detecting"

print("Noise protection : OK")

# ----------------------------------------------------------
# Bicep curl confirmation
# ----------------------------------------------------------

stabilizer.update(
    "bicep_curl",
    0.90,
    "right",
)

stabilizer.update(
    "bicep_curl",
    0.93,
    "right",
)

result = stabilizer.update(
    "bicep_curl",
    0.94,
    "right",
)

print("Bicep confirmation:", result)

assert result["exercise"] == "bicep_curl"
assert result["side"] == "right"
assert result["status"] == "confirmed"

print("Exercise switching : OK")

# ----------------------------------------------------------
# Low confidence
# ----------------------------------------------------------

result = stabilizer.update(
    "lunge",
    0.30,
    "right",
)

print("Low confidence:", result)

assert result["status"] == "waiting"
assert stabilizer.get_current_exercise() == "bicep_curl"

print("Confidence filtering : OK")

# ----------------------------------------------------------
# Reset
# ----------------------------------------------------------

stabilizer.reset()

assert stabilizer.get_current_exercise() is None
assert stabilizer.get_candidate_exercise() is None
assert stabilizer.get_candidate_frames() == 0
assert stabilizer.is_confirmed() is False

print("Reset : OK")

print("-------------------------")
print("Detection Stabilizer Test PASSED")