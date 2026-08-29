"""
Speech Queue Test
"""

from voice_engine.voice_events import (
    exercise_started,
    rep_completed,
)

from voice_engine.speech_queue import SpeechQueue


print("Speech Queue Test")
print("-----------------")

# ==========================================================
# CREATE QUEUE
# ==========================================================

queue = SpeechQueue()

print("Queue created : OK")

assert queue.is_empty()
assert queue.size() == 0

# ==========================================================
# ADD EVENTS
# ==========================================================

event1 = exercise_started("bicep_curl")
event2 = rep_completed("bicep_curl", 1)
event3 = rep_completed("bicep_curl", 2)

assert queue.put(event1)
assert queue.put(event2)
assert queue.put(event3)

print("Events added  : OK")

assert queue.size() == 3
assert not queue.is_empty()

# ==========================================================
# PEEK
# ==========================================================

peeked = queue.peek()

print("Peek event    :", peeked)

assert peeked["type"] == "exercise_started"
assert queue.size() == 3

print("Peek          : OK")

# ==========================================================
# GET
# ==========================================================

first = queue.get()

print("First event   :", first)

assert first["type"] == "exercise_started"
assert queue.size() == 2

print("FIFO order    : OK")

# ==========================================================
# GET NEXT
# ==========================================================

second = queue.get()

assert second["type"] == "rep_completed"
assert second["rep"] == 1

third = queue.get()

assert third["type"] == "rep_completed"
assert third["rep"] == 2

print("Remaining FIFO: OK")

# ==========================================================
# EMPTY GET
# ==========================================================

assert queue.get() is None

print("Empty get     : OK")

# ==========================================================
# CLEAR
# ==========================================================

queue.put(rep_completed("squat", 1))
queue.put(rep_completed("squat", 2))

assert queue.size() == 2

queue.clear()

assert queue.is_empty()
assert queue.size() == 0

print("Clear         : OK")

# ==========================================================
# MAX SIZE
# ==========================================================

limited_queue = SpeechQueue(max_size=2)

limited_queue.put(rep_completed("squat", 1))
limited_queue.put(rep_completed("squat", 2))
limited_queue.put(rep_completed("squat", 3))

assert limited_queue.size() == 2

oldest = limited_queue.get()

assert oldest["rep"] == 2

print("Max size      : OK")

# ==========================================================
# NONE HANDLING
# ==========================================================

assert not queue.put(None)

print("None handling : OK")

# ==========================================================
# FINAL
# ==========================================================

print("-----------------")
print("Speech Queue Test PASSED")