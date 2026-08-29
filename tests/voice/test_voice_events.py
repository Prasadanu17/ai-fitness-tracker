"""
Voice Events Test

Tests the event layer used by the Voice Engine.

The event layer should:
    - Create exercise announcement events.
    - Create rep announcement events.
    - Create feedback events.
    - Create ready/waiting events.
    - Return predictable dictionaries.
"""

from voice_engine.voice_events import (
    exercise_started,
    rep_completed,
    feedback_message,
    waiting_for_exercise,
)


print("Voice Events Test")
print("-----------------")

# ----------------------------------------------------------
# Exercise started
# ----------------------------------------------------------

event = exercise_started("bicep_curl")

print("Exercise event :", event)

assert event["type"] == "exercise_started"
assert event["exercise"] == "bicep_curl"

print("Exercise event : OK")


# ----------------------------------------------------------
# Rep completed
# ----------------------------------------------------------

event = rep_completed("bicep_curl", 1)

print("Rep event      :", event)

assert event["type"] == "rep_completed"
assert event["exercise"] == "bicep_curl"
assert event["rep"] == 1

print("Rep event      : OK")


# ----------------------------------------------------------
# Feedback
# ----------------------------------------------------------

event = feedback_message(
    "Keep your back straight"
)

print("Feedback event :", event)

assert event["type"] == "feedback"
assert event["message"] == "Keep your back straight"

print("Feedback event : OK")


# ----------------------------------------------------------
# Waiting
# ----------------------------------------------------------

event = waiting_for_exercise()

print("Waiting event  :", event)

assert event["type"] == "waiting"

print("Waiting event  : OK")


print("-----------------")
print("Voice Events Test PASSED")