"""
Live Workout Unit Test
"""

from ai_engine.live_workout import LiveWorkout


print("Live Workout Test")
print("------------------")


# ==========================================================
# CREATE
# ==========================================================

live = LiveWorkout()

print(
    "Live workout created :",
    "OK"
)


# ==========================================================
# START
# ==========================================================

status = live.start(
    "squat",
    side="right"
)

print(
    "Workout started      :",
    "OK" if live.is_running() else "FAILED"
)

print(
    "Exercise             :",
    status["exercise"]
)


# ==========================================================
# STATUS
# ==========================================================

current_status = live.get_status()

print(
    "Status available     :",
    "OK" if current_status["active"] else "FAILED"
)


# ==========================================================
# RESET
# ==========================================================

live.reset()

print(
    "Reset                :",
    "OK"
)


# ==========================================================
# STOP
# ==========================================================

live.stop()

print(
    "Workout stopped      :",
    "OK" if not live.is_running() else "FAILED"
)


# ==========================================================
# CLOSE
# ==========================================================

live.close()

print(
    "Resources released   :",
    "OK"
)


print("------------------")
print("Live Workout Test PASSED")