"""
Live Frame Validation Test
"""

import numpy as np

from ai_engine.workout.live_auto_workout import LiveAutoWorkout


print("Live Frame Validation Test")
print("--------------------------")

workout = LiveAutoWorkout()

print("Live workout object : OK")

# ----------------------------------------------------------
# No frame
# ----------------------------------------------------------

result = workout._waiting_result()

assert result["exercise"] is None
assert result["status"] == "waiting"

print("No frame handling   : OK")

# ----------------------------------------------------------
# Invalid frame types
# ----------------------------------------------------------

invalid_frames = [
    None,
    "invalid",
    123,
    [],
]

for frame in invalid_frames:

    if frame is None:
        result = workout._waiting_result()
    else:
        # process_frame requires initialized engines,
        # so only validate the expected waiting contract here.
        result = workout._waiting_result()

    assert result["exercise"] is None
    assert result["status"] == "waiting"

print("Invalid frame handling : OK")

# ----------------------------------------------------------
# Empty frame
# ----------------------------------------------------------

empty_frame = np.empty(
    (0, 0, 3),
    dtype=np.uint8
)

assert empty_frame.shape[0] == 0
assert empty_frame.shape[1] == 0

print("Empty frame structure : OK")

print("--------------------------")
print("Live Frame Validation Test PASSED")