"""
AI Fitness Tracker Voice Engine
"""

from .voice_events import (
    VoiceEvent,
    exercise_started,
    exercise_changed,
    rep_completed,
    feedback_message,
    waiting_for_exercise,
    workout_started,
    workout_stopped,
    workout_reset,
)

from .speech_queue import SpeechQueue
from .speech_worker import SpeechWorker
from .voice_controller import VoiceController


__all__ = [
    "VoiceEvent",

    "exercise_started",
    "exercise_changed",
    "rep_completed",
    "feedback_message",
    "waiting_for_exercise",
    "workout_started",
    "workout_stopped",
    "workout_reset",

    "SpeechQueue",
    "SpeechWorker",
    "VoiceController",
]