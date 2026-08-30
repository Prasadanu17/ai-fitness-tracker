"""
Voice Controller

Connects workout results to the asynchronous speech system.

Responsibilities:
    - Announce workout start.
    - Announce exercise detection.
    - Announce exercise changes.
    - Announce completed repetitions.
    - Announce meaningful form corrections.
    - Announce waiting state.
    - Prevent duplicate announcements.
    - Reset safely.
"""

from voice_engine.voice_events import (
    workout_started,
    workout_stopped,
    workout_reset,
    exercise_started,
    exercise_changed,
    rep_completed,
    feedback_message,
    waiting_for_exercise,
)


class VoiceController:

    def __init__(
        self,
        speech_queue,
        min_confidence=0.70,
    ):

        if speech_queue is None:
            raise ValueError(
                "speech_queue cannot be None"
            )

        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError(
                "min_confidence must be between 0.0 and 1.0"
            )

        self.queue = speech_queue
        self.min_confidence = min_confidence

        self.current_exercise = None
        self.current_side = None
        self.current_rep = 0

        self.last_feedback = None

        self.is_waiting_announced = False

    # ==========================================================
    # WORKOUT EVENTS
    # ==========================================================

    def announce_workout_started(self):

        event = workout_started()

        self.queue.put(event)

        return event

    def announce_workout_stopped(self):

        event = workout_stopped()

        self.queue.put(event)

        return event

    def announce_workout_reset(self):

        event = workout_reset()

        self.queue.put(event)

        return event

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, result):

        if not isinstance(result, dict):
            return []

        events = []

        exercise = result.get(
            "exercise"
        )

        detected_exercise = result.get(
            "detected_exercise"
        )

        confidence = result.get(
            "confidence",
            result.get(
                "detected_confidence",
                0.0,
            ),
        )

        side = result.get(
            "side",
            result.get(
                "detected_side"
            ),
        )

        reps = result.get(
            "reps",
            0,
        )

        form = result.get(
            "form"
        )

        status = str(
            result.get(
                "status",
                "",
            )
        ).strip().lower()

        # ------------------------------------------------------
        # Safe confidence
        # ------------------------------------------------------

        try:
            confidence = float(
                confidence
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        # ------------------------------------------------------
        # Safe reps
        # ------------------------------------------------------

        try:
            reps = int(
                reps
            )
        except (
            TypeError,
            ValueError,
        ):
            reps = 0

        reps = max(
            0,
            reps,
        )

        # ======================================================
        # WAITING
        # ======================================================

        if (
            exercise is None
            and detected_exercise is None
        ):

            event = self._announce_waiting()

            if event is not None:
                events.append(event)

            return events

        if status in {
            "waiting",
            "waiting_for_exercise",
        } and exercise is None:

            event = self._announce_waiting()

            if event is not None:
                events.append(event)

            return events

        # ======================================================
        # CONFIDENCE
        # ======================================================

        if confidence < self.min_confidence:
            return events

        # ======================================================
        # ACTIVE EXERCISE
        # ======================================================

        active_exercise = (
            exercise
            or detected_exercise
        )

        if active_exercise is None:
            return events

        active_exercise = str(
            active_exercise
        ).strip().lower()

        if not active_exercise:
            return events

        # ======================================================
        # FIRST EXERCISE
        # ======================================================

        if self.current_exercise is None:

            event = exercise_started(
                active_exercise,
                confidence=confidence,
                side=side,
            )

            self.queue.put(event)

            events.append(event)

            self.current_exercise = (
                active_exercise
            )

            self.current_side = side
            self.current_rep = 0
            self.last_feedback = None

        # ======================================================
        # EXERCISE CHANGE
        # ======================================================

        elif active_exercise != self.current_exercise:

            event = exercise_changed(
                active_exercise,
                confidence=confidence,
                side=side,
            )

            self.queue.put(event)

            events.append(event)

            self.current_exercise = (
                active_exercise
            )

            self.current_side = side
            self.current_rep = 0
            self.last_feedback = None

        else:

            if side is not None:
                self.current_side = side

        # ======================================================
        # REP ANNOUNCEMENTS
        # ======================================================

        if reps > self.current_rep:

            for rep_number in range(
                self.current_rep + 1,
                reps + 1,
            ):

                event = rep_completed(
                    active_exercise,
                    rep_number,
                )

                self.queue.put(event)

                events.append(event)

            self.current_rep = reps

        # ======================================================
        # FORM FEEDBACK
        # ======================================================

        feedback = self._normalize_feedback(
            form
        )

        if feedback is not None:

            event = self._announce_feedback(
                feedback
            )

            if event is not None:
                events.append(event)

        self.is_waiting_announced = False

        return events

    # ==========================================================
    # FEEDBACK NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_feedback(form):

        if form is None:
            return None

        message = str(
            form
        ).strip()

        if not message:
            return None

        ignored_messages = {
            "good",
            "great",
            "excellent",
            "correct",
            "ok",
            "okay",
            "perfect",
            "waiting",
            "none",
        }

        if message.lower() in ignored_messages:
            return None

        return message

    # ==========================================================
    # FEEDBACK
    # ==========================================================

    def _announce_feedback(self, message):

        if message == self.last_feedback:
            return None

        event = feedback_message(
            message
        )

        self.queue.put(event)

        self.last_feedback = message

        return event

    # ==========================================================
    # WAITING
    # ==========================================================

    def _announce_waiting(self):

        if self.is_waiting_announced:
            return None

        event = waiting_for_exercise()

        self.queue.put(event)

        self.is_waiting_announced = True

        return event

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.current_exercise = None
        self.current_side = None
        self.current_rep = 0

        self.last_feedback = None

        self.is_waiting_announced = False

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self):

        self.reset()

        self.queue.clear()

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_current_exercise(self):
        return self.current_exercise

    def get_current_rep(self):
        return self.current_rep

    def get_current_side(self):
        return self.current_side

    def get_last_feedback(self):
        return self.last_feedback