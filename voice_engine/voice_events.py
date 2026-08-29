"""
Voice Events

Defines standardized events used by the AI Fitness Tracker
voice system.

The voice layer is intentionally separated from the workout
engine so speech processing can later run asynchronously
without slowing down pose detection or rep counting.
"""


class VoiceEvent(dict):
    """
    Standard voice event.

    Behaves like a normal dictionary so existing code can use:

        event["type"]
        event["message"]

    Example:

        VoiceEvent(
            type="rep_completed",
            exercise="bicep_curl",
            rep=1,
            message="Rep 1"
        )
    """

    def __init__(
        self,
        type,
        message,
        exercise=None,
        rep=None,
        confidence=None,
        side=None,
    ):
        super().__init__(
            type=type,
            message=message,
            exercise=exercise,
            rep=rep,
            confidence=confidence,
            side=side,
        )

    @property
    def event_type(self):
        """Return the event type."""
        return self["type"]

    @property
    def message(self):
        """Return the voice message."""
        return self["message"]

    @property
    def exercise(self):
        """Return the exercise name."""
        return self["exercise"]

    @property
    def rep(self):
        """Return the repetition number."""
        return self["rep"]


# ==========================================================
# EXERCISE STARTED
# ==========================================================

def exercise_started(
    exercise,
    confidence=None,
    side=None,
):
    """
    Create an exercise-started voice event.

    Example:

        exercise_started("bicep_curl")

    Produces:

        Exercise: bicep curl
    """

    exercise_name = str(exercise).strip().lower()

    display_name = exercise_name.replace("_", " ")

    return VoiceEvent(
        type="exercise_started",
        exercise=exercise_name,
        confidence=confidence,
        side=side,
        message=f"Exercise: {display_name}",
    )


# ==========================================================
# REP COMPLETED
# ==========================================================

def rep_completed(
    exercise,
    rep,
):
    """
    Create a completed-repetition voice event.

    Example:

        rep_completed("bicep_curl", 1)

    Produces:

        Rep 1
    """

    exercise_name = str(exercise).strip().lower()

    return VoiceEvent(
        type="rep_completed",
        exercise=exercise_name,
        rep=int(rep),
        message=f"Rep {int(rep)}",
    )


# ==========================================================
# FORM FEEDBACK
# ==========================================================

def feedback_message(message):
    """
    Create a form-feedback voice event.

    Example:

        feedback_message(
            "Keep your back straight"
        )
    """

    if message is None:
        message = ""

    message = str(message).strip()

    return VoiceEvent(
        type="feedback",
        message=message,
    )


# ==========================================================
# WAITING
# ==========================================================

def waiting_for_exercise():
    """
    Create a waiting-for-exercise event.

    Used when the camera sees a person but no supported
    exercise has been confidently detected.
    """

    return VoiceEvent(
        type="waiting",
        message="Waiting for exercise",
    )


# ==========================================================
# EXERCISE CHANGED
# ==========================================================

def exercise_changed(
    exercise,
    confidence=None,
    side=None,
):
    """
    Create an exercise-change event.

    This is different from exercise_started because the
    workout may already be running.

    Example:

        squat -> bicep curl
    """

    exercise_name = str(exercise).strip().lower()

    display_name = exercise_name.replace("_", " ")

    return VoiceEvent(
        type="exercise_changed",
        exercise=exercise_name,
        confidence=confidence,
        side=side,
        message=f"Exercise: {display_name}",
    )


# ==========================================================
# WORKOUT STARTED
# ==========================================================

def workout_started():
    """
    Create a workout-started event.
    """

    return VoiceEvent(
        type="workout_started",
        message="Workout started",
    )


# ==========================================================
# WORKOUT STOPPED
# ==========================================================

def workout_stopped():
    """
    Create a workout-stopped event.
    """

    return VoiceEvent(
        type="workout_stopped",
        message="Workout stopped",
    )


# ==========================================================
# RESET
# ==========================================================

def workout_reset():
    """
    Create a workout-reset event.
    """

    return VoiceEvent(
        type="workout_reset",
        message="Workout reset",
    )