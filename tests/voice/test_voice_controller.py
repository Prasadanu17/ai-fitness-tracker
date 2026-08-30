"""
Voice Controller Test
"""

from voice_engine.speech_queue import SpeechQueue

from voice_engine.voice_controller import (
    VoiceController,
)


print("Voice Controller Test")
print("---------------------")


# ==========================================================
# SETUP
# ==========================================================

queue = SpeechQueue()

controller = VoiceController(
    queue,
    min_confidence=0.70,
)

print("Queue created      : OK")
print("Controller created : OK")


# ==========================================================
# FIRST EXERCISE
# ==========================================================

result = {
    "exercise": "squat",
    "detected_exercise": "squat",
    "confidence": 0.92,
    "side": "right",
    "status": "active",
    "reps": 0,
    "state": "UP",
    "form": "Good",
}

events = controller.process(
    result
)

assert len(events) >= 1
assert controller.get_current_exercise() == "squat"

assert events[0]["type"] == (
    "exercise_started"
)

print("Exercise detection : OK")
print("Exercise event      :", events[0])


# ==========================================================
# DUPLICATE PROTECTION
# ==========================================================

queue.clear()

events = controller.process(
    result
)

assert len(events) == 0
assert queue.is_empty()

print("Duplicate protection: OK")


# ==========================================================
# REP 1
# ==========================================================

result["reps"] = 1

events = controller.process(
    result
)

assert len(events) == 1
assert events[0]["type"] == (
    "rep_completed"
)
assert events[0]["rep"] == 1

print("Rep 1 announcement  : OK")


# ==========================================================
# REP 2
# ==========================================================

events = controller.process(
    {
        **result,
        "reps": 2,
    }
)

assert len(events) == 1
assert events[0]["type"] == (
    "rep_completed"
)
assert events[0]["rep"] == 2

print("Rep 2 announcement  : OK")


# ==========================================================
# SAME REP / SAME FRAME
# ==========================================================

events = controller.process(
    {
        **result,
        "reps": 2,
    }
)

assert len(events) == 0

print("Rep duplicate guard : OK")


# ==========================================================
# FEEDBACK
# ==========================================================

events = controller.process(
    {
        **result,
        "reps": 2,
        "form": "Keep your back straight",
    }
)

assert len(events) == 1
assert events[0]["type"] == "feedback"

print("Feedback event      : OK")


# ==========================================================
# DUPLICATE FEEDBACK
# ==========================================================

events = controller.process(
    {
        **result,
        "reps": 2,
        "form": "Keep your back straight",
    }
)

assert len(events) == 0

print("Feedback guard      : OK")


# ==========================================================
# NEW FEEDBACK
# ==========================================================

events = controller.process(
    {
        **result,
        "reps": 2,
        "form": "Go a little deeper",
    }
)

assert len(events) == 1
assert events[0]["type"] == "feedback"

print("New feedback        : OK")


# ==========================================================
# EXERCISE SWITCH
# ==========================================================

events = controller.process(
    {
        "exercise": "bicep_curl",
        "detected_exercise": "bicep_curl",
        "confidence": 0.95,
        "side": "right",
        "status": "active",
        "reps": 0,
        "state": "UP",
        "form": "Good",
    }
)

assert controller.get_current_exercise() == (
    "bicep_curl"
)

assert len(events) == 1

# Switching exercise must produce
# exercise_changed, NOT exercise_started.
assert events[0]["type"] == (
    "exercise_changed"
)

print("Exercise switching  : OK")


# ==========================================================
# LOW CONFIDENCE
# ==========================================================

queue.clear()

events = controller.process(
    {
        "exercise": "lunge",
        "detected_exercise": "lunge",
        "confidence": 0.30,
        "side": "right",
        "status": "detecting",
        "reps": 0,
        "state": "UP",
        "form": "Good",
    }
)

assert len(events) == 0

# Low-confidence detection must NOT
# change the currently active exercise.
assert controller.get_current_exercise() == (
    "bicep_curl"
)

print("Confidence filtering: OK")


# ==========================================================
# WAITING
# ==========================================================

controller.reset()
queue.clear()

events = controller.process(
    {
        "exercise": None,
        "detected_exercise": None,
        "confidence": 0.0,
        "side": None,
        "status": "waiting",
        "reps": 0,
        "state": "UP",
        "form": "Waiting",
    }
)

assert len(events) == 1
assert events[0]["type"] == "waiting"

print("Waiting event       : OK")


# ==========================================================
# WAITING DUPLICATE
# ==========================================================

events = controller.process(
    {
        "exercise": None,
        "detected_exercise": None,
        "confidence": 0.0,
        "side": None,
        "status": "waiting",
        "reps": 0,
        "state": "UP",
        "form": "Waiting",
    }
)

assert len(events) == 0

print("Waiting guard       : OK")


# ==========================================================
# RESET
# ==========================================================

controller.reset()

assert controller.get_current_exercise() is None
assert controller.get_current_rep() == 0
assert controller.get_current_side() is None
assert controller.get_last_feedback() is None

print("Reset               : OK")


# ==========================================================
# FINAL
# ==========================================================

print("---------------------")
print("Voice Controller Test PASSED")