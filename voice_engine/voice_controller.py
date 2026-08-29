"""
Voice Controller

Connects workout results to the voice-event and speech layers.

Responsibilities:
    - Announce detected exercises.
    - Announce completed repetitions.
    - Announce form feedback.
    - Prevent duplicate announcements.
    - Handle exercise switching.
    - Handle waiting state.
    - Filter low-confidence detections.
    - Reset safely.

Architecture:

    AutoWorkoutEngine
            |
            v
      VoiceController
            |
            v
       Voice Events
            |
            v
       Speech Queue
            |
            v
       Speech Worker
"""

from voice_engine.voice_events import (
    exercise_started,
    rep_completed,
    feedback_message,
    waiting_for_exercise,
)


class VoiceController:

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        speech_queue,
        min_confidence=0.70,
    ):
        """
        Parameters
        ----------
        speech_queue:
            SpeechQueue instance.

        min_confidence:
            Minimum detection confidence required
            before announcing an exercise.
        """

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

        # Current workout state
        self.current_exercise = None
        self.current_side = None
        self.current_rep = 0

        # Feedback protection
        self.last_feedback = None

        # Waiting protection
        self.is_waiting_announced = False

    # ==========================================================
    # MAIN PROCESS
    # ==========================================================

    def process(self, result):
        """
        Process one workout result.

        Expected input:

            {
                "exercise": "squat",
                "detected_exercise": "squat",
                "confidence": 0.92,
                "side": "right",
                "status": "active",
                "reps": 3,
                "state": "UP",
                "form": "Good"
            }

        Returns
        -------
        list
            Voice events generated during this frame.
        """

        if not isinstance(result, dict):
            return []

        events = []

        # ------------------------------------------------------
        # READ RESULT
        # ------------------------------------------------------

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
                0.0
            )
        )

        side = result.get(
            "side",
            result.get(
                "detected_side"
            )
        )

        reps = result.get(
            "reps",
            0
        )

        form = result.get(
            "form"
        )

        # ------------------------------------------------------
        # SAFE CONFIDENCE
        # ------------------------------------------------------

        try:
            confidence = float(
                confidence
            )
        except (
            TypeError,
            ValueError
        ):
            confidence = 0.0

        # ------------------------------------------------------
        # SAFE REP COUNT
        # ------------------------------------------------------

        try:
            reps = int(
                reps
            )
        except (
            TypeError,
            ValueError
        ):
            reps = 0

        if reps < 0:
            reps = 0

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

        # ======================================================
        # CONFIDENCE FILTER
        # ======================================================

        if confidence < self.min_confidence:
            return events

        # ======================================================
        # DETERMINE ACTIVE EXERCISE
        # ======================================================

        active_exercise = (
            exercise
            or detected_exercise
        )

        if active_exercise is None:
            return events

        active_exercise = (
            str(active_exercise)
            .strip()
            .lower()
        )

        if not active_exercise:
            return events

        # ======================================================
        # EXERCISE START / SWITCH
        # ======================================================

        if (
            active_exercise
            != self.current_exercise
        ):

            event = exercise_started(
                active_exercise,
                confidence=confidence,
                side=side,
            )

            self.queue.put(
                event
            )

            events.append(
                event
            )

            # Update active exercise
            self.current_exercise = (
                active_exercise
            )

            self.current_side = side

            # New exercise starts its own rep sequence
            self.current_rep = 0

            # Allow new feedback
            self.last_feedback = None

        # ======================================================
        # REP ANNOUNCEMENTS
        # ======================================================

        if reps > self.current_rep:

            for rep_number in range(
                self.current_rep + 1,
                reps + 1
            ):

                event = rep_completed(
                    active_exercise,
                    rep_number,
                )

                self.queue.put(
                    event
                )

                events.append(
                    event
                )

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

        # ======================================================
        # ACTIVE STATE
        # ======================================================

        self.is_waiting_announced = False

        return events

    # ==========================================================
    # FEEDBACK NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize_feedback(form):
        """
        Convert form information into useful voice feedback.

        Generic positive messages are ignored because we don't
        want the assistant repeatedly saying "Good" every frame.
        """

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
            "waiting",
        }

        if message.lower() in ignored_messages:
            return None

        return message

    # ==========================================================
    # FEEDBACK ANNOUNCEMENT
    # ==========================================================

    def _announce_feedback(
        self,
        message,
    ):
        """
        Announce feedback only when it changes.
        """

        if (
            message
            == self.last_feedback
        ):
            return None

        event = feedback_message(
            message
        )

        self.queue.put(
            event
        )

        self.last_feedback = message

        return event

    # ==========================================================
    # WAITING ANNOUNCEMENT
    # ==========================================================

    def _announce_waiting(self):
        """
        Announce waiting state only once.
        """

        if self.is_waiting_announced:
            return None

        event = waiting_for_exercise()

        self.queue.put(
            event
        )

        self.is_waiting_announced = True

        return event

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset controller state.

        Does not clear the speech queue.
        """

        self.current_exercise = None
        self.current_side = None
        self.current_rep = 0

        self.last_feedback = None

        self.is_waiting_announced = False

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self):
        """
        Reset controller and clear pending speech events.
        """

        self.reset()

        self.queue.clear()

    # ==========================================================
    # GET CURRENT EXERCISE
    # ==========================================================

    def get_current_exercise(self):
        return self.current_exercise

    # ==========================================================
    # GET CURRENT REP
    # ==========================================================

    def get_current_rep(self):
        return self.current_rep

    # ==========================================================
    # GET CURRENT SIDE
    # ==========================================================

    def get_current_side(self):
        return self.current_side

    # ==========================================================
    # GET LAST FEEDBACK
    # ==========================================================

    def get_last_feedback(self):
        return self.last_feedback