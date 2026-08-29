"""
Speech Worker Test
"""

from voice_engine.speech_queue import SpeechQueue

from voice_engine.speech_worker import (
    SpeechWorker,
)

from voice_engine.voice_events import (
    exercise_started,
    rep_completed,
)


print("Speech Worker Test")
print("------------------")


# ==========================================================
# QUEUE
# ==========================================================

queue = SpeechQueue()

print("Queue created  : OK")


# ==========================================================
# WORKER
# ==========================================================

worker = SpeechWorker(
    queue,
    rate=175,
    volume=1.0,
)

assert worker is not None

print("Worker created : OK")


# ==========================================================
# ADD EVENTS
# ==========================================================

queue.put(
    exercise_started(
        "bicep_curl"
    )
)

queue.put(
    rep_completed(
        "bicep_curl",
        1
    )
)

queue.put(
    rep_completed(
        "bicep_curl",
        2
    )
)

print("Events queued  : OK")

assert queue.size() == 3


# ==========================================================
# START
# ==========================================================

started = worker.start()

assert started
assert worker.is_running()

print("Worker started : OK")


# ==========================================================
# WAIT FOR SPEECH
# ==========================================================

spoken = worker.wait_until_empty(
    timeout=15
)

assert spoken

print("Events spoken  : OK")


# ==========================================================
# STOP
# ==========================================================

worker.stop()

assert not worker.is_running()

print("Worker stopped : OK")


# ==========================================================
# RESTART
# ==========================================================

started_again = worker.start()

assert started_again
assert worker.is_running()

print("Worker restart : OK")

worker.stop()


# ==========================================================
# NONE HANDLING
# ==========================================================

assert queue.put(None) is False

print("None handling  : OK")


# ==========================================================
# FINAL
# ==========================================================

print("------------------")
print("Speech Worker Test PASSED")