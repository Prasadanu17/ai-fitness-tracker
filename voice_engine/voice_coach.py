"""
Voice Coach

Generates short, natural, motivating voice-coaching messages
for the AI GYM Tracker.

Responsibilities:
    - Encourage the user when an exercise starts.
    - Give motivating messages after completed reps.
    - Provide exercise-specific coaching.
    - Soften form corrections into natural spoken guidance.
    - Announce exercise transitions naturally.
    - Avoid repetitive coaching messages.
    - Remain lightweight and fully local.

This class does NOT perform:
    - pose detection
    - exercise detection
    - rep counting
    - exercise selection
    - speech synthesis

It only creates the text that is passed to the existing
VoiceController -> SpeechQueue -> SpeechWorker pipeline.
"""

import random


class VoiceCoach:
    """
    Lightweight rule-based AI-style voice coach.

    The class intentionally does not call an external LLM or API.
    It generates contextual coaching locally so the live workout
    remains responsive and does not require an API key.
    """

    # ==========================================================
    # EXERCISE START MESSAGES
    # ==========================================================

    START_MESSAGES = {
        "squat": [
            "Let's get started. Keep your chest up and move smoothly.",
            "Ready for squats? Keep your feet steady and control every rep.",
            "Great, let's work on those squats. Stay balanced and keep your movement smooth.",
        ],
        "bicep_curl": [
            "Let's work those arms. Keep your elbow steady and curl smoothly.",
            "Ready for curls? Keep your upper arm still and control the movement.",
            "Great, let's start. Keep your elbow close and avoid swinging.",
        ],
        "lunge": [
            "Let's get started with lunges. Stay balanced and take your time.",
            "Ready for lunges? Keep your chest up and control each step.",
            "Great, let's work on those lunges. Stay tall and move with control.",
        ],
    }

    # ==========================================================
    # EXERCISE CHANGE MESSAGES
    # ==========================================================

    CHANGE_MESSAGES = {
        "squat": [
            "Nice transition. We're moving into squats now.",
            "Good work. Let's focus on controlled squats.",
        ],
        "bicep_curl": [
            "Nice work. Now let's focus on your curls.",
            "Good transition. Keep those curls controlled.",
        ],
        "lunge": [
            "Great work. Now let's move into lunges.",
            "Nice transition. Stay balanced as we work on lunges.",
        ],
    }

    # ==========================================================
    # REP MESSAGES
    # ==========================================================

    REP_MESSAGES = {
        "squat": [
            "Nice work, rep {rep}.",
            "Great squat, rep {rep}. Keep that control.",
            "Good job, rep {rep}. Keep your chest up.",
            "Strong rep {rep}. Stay smooth.",
        ],
        "bicep_curl": [
            "Nice curl, rep {rep}.",
            "Great job, rep {rep}. Keep your elbow steady.",
            "Good work, rep {rep}. Stay controlled.",
            "Strong curl, rep {rep}. Keep avoiding the swing.",
        ],
        "lunge": [
            "Nice lunge, rep {rep}.",
            "Great work, rep {rep}. Stay balanced.",
            "Good job, rep {rep}. Keep your chest up.",
            "Strong rep {rep}. Keep that control.",
        ],
    }

    # ==========================================================
    # MILESTONE MESSAGES
    # ==========================================================

    MILESTONES = {
        5: [
            "Five reps! Nice work. Keep going.",
            "That's five. You're doing great.",
        ],
        10: [
            "Ten reps! Excellent work. Keep that rhythm.",
            "Ten reps down. Strong work, keep going.",
        ],
        15: [
            "Fifteen reps! You're doing really well.",
            "Great consistency. Fifteen reps completed.",
        ],
        20: [
            "Twenty reps! Fantastic work.",
            "Twenty reps done. You're on fire.",
        ],
    }

    # ==========================================================
    # GENERAL FEEDBACK
    # ==========================================================

    FEEDBACK_PREFIXES = [
        "Nice adjustment.",
        "Good correction.",
        "You're doing well.",
        "Small adjustment.",
    ]

    # ==========================================================
    # WAITING STATE MESSAGES
    # ==========================================================

    WAITING_MESSAGES = [
        "I'm ready when you are. Get into position.",
        "Take your time getting ready. Let me know when you're set.",
        "Waiting for you to begin your exercise.",
        "Get into starting position whenever you're ready.",
        "I'm ready to track your exercise. Let me see your full body.",
    ]

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, debug=False):
        self.debug = bool(debug)

        self.current_exercise = None
        self.last_rep_message = None
        self.last_feedback = None

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _normalize_exercise(exercise):
        if exercise is None:
            return None

        value = str(exercise).strip().lower()

        aliases = {
            "bicep curl": "bicep_curl",
            "bicep-curl": "bicep_curl",
            "curl": "bicep_curl",
            "squats": "squat",
            "lunges": "lunge",
        }

        return aliases.get(value, value)

    @staticmethod
    def _choose(messages):
        if not messages:
            return None

        return random.choice(messages)

    # ==========================================================
    # EXERCISE START
    # ==========================================================

    def on_exercise_started(self, exercise):
        """
        Return a natural spoken message when an exercise starts.
        """

        exercise = self._normalize_exercise(exercise)

        self.current_exercise = exercise
        self.last_rep_message = None
        self.last_feedback = None

        messages = self.START_MESSAGES.get(exercise)

        message = self._choose(messages)

        if self.debug:
            print(
                f"[VOICE COACH] exercise started: "
                f"{exercise} -> {message}"
            )

        return message

    # ==========================================================
    # EXERCISE CHANGE
    # ==========================================================

    def on_exercise_changed(self, exercise):
        """
        Return a natural transition message.
        """

        exercise = self._normalize_exercise(exercise)

        self.current_exercise = exercise
        self.last_rep_message = None
        self.last_feedback = None

        messages = self.CHANGE_MESSAGES.get(exercise)

        message = self._choose(messages)

        if self.debug:
            print(
                f"[VOICE COACH] exercise changed: "
                f"{exercise} -> {message}"
            )

        return message

    # ==========================================================
    # REP COMPLETED
    # ==========================================================

    def on_rep_completed(self, exercise, rep):
        """
        Return a short motivating message for a completed rep.
        """

        exercise = self._normalize_exercise(exercise)

        try:
            rep = int(rep)
        except (TypeError, ValueError):
            return None

        if rep <= 0:
            return None

        # ------------------------------------------------------
        # Milestone coaching
        # ------------------------------------------------------

        if rep in self.MILESTONES:
            message = self._choose(
                self.MILESTONES[rep]
            )

            self.last_rep_message = message

            if self.debug:
                print(
                    f"[VOICE COACH] milestone: "
                    f"{rep} -> {message}"
                )

            return message

        # ------------------------------------------------------
        # Exercise-specific rep coaching
        # ------------------------------------------------------

        messages = self.REP_MESSAGES.get(
            exercise
        )

        if not messages:
            message = f"Nice work, rep {rep}."
        else:
            message = self._choose(
                messages
            ).format(
                rep=rep
            )

        self.last_rep_message = message

        if self.debug:
            print(
                f"[VOICE COACH] rep: "
                f"{exercise} #{rep} -> {message}"
            )

        return message

    # ==========================================================
    # FORM FEEDBACK
    # ==========================================================

    def on_form_feedback(self, message):
        """
        Turn raw form feedback into a softer coaching message.

        Example:

            "Keep your back straight"

        becomes something like:

            "Nice adjustment. Keep your back straight."
        """

        if message is None:
            return None

        text = str(message).strip()

        if not text:
            return None

        # Avoid double punctuation.
        text = text.rstrip(".!?")

        prefix = self._choose(
            self.FEEDBACK_PREFIXES
        )

        coached_message = (
            f"{prefix} {text}."
        )

        # Do not repeatedly speak identical feedback.
        if coached_message == self.last_feedback:
            return None

        self.last_feedback = coached_message

        if self.debug:
            print(
                f"[VOICE COACH] feedback -> "
                f"{coached_message}"
            )

        return coached_message

    # ==========================================================
    # WAITING STATE
    # ==========================================================

    def on_waiting_for_exercise(self):
        """
        Return a patient, non-aggressive waiting message.
        """

        message = self._choose(
            self.WAITING_MESSAGES
        )

        if self.debug:
            print(
                f"[VOICE COACH] waiting -> {message}"
            )

        return message

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset coaching state.
        """

        self.current_exercise = None
        self.last_rep_message = None
        self.last_feedback = None

    # ==========================================================
    # DEBUG / STATE
    # ==========================================================

    def get_current_exercise(self):
        return self.current_exercise

    def get_last_rep_message(self):
        return self.last_rep_message

    def get_last_feedback(self):
        return self.last_feedback