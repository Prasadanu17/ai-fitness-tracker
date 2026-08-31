"""
Voice Controller

Connects workout results to the asynchronous speech system.

Responsibilities:
    - Announce workout start.
    - Announce workout stop.
    - Announce workout reset.
    - Announce first exercise detection.
    - Announce exercise changes.
    - Announce completed repetitions.
    - Announce meaningful form corrections.
    - Announce waiting state.
    - Prevent duplicate announcements.
    - Filter low-confidence detections.
    - Reset safely.

Integration with VoiceCoach:
    The VoiceCoach generates intelligent, contextual coaching messages
    that are used instead of generic event messages when available.
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

from voice_engine.voice_coach import VoiceCoach


class VoiceController:

    def __init__(
        self,
        speech_queue,
        min_confidence=0.70,
        voice_coach=None,
        debug=False,
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

        self.min_confidence = float(
            min_confidence
        )

        self.debug = bool(debug)

        # ------------------------------------------------------
        # Voice Coach
        # ------------------------------------------------------

        if voice_coach is None:
            self.coach = VoiceCoach(
                debug=debug
            )
        else:
            self.coach = voice_coach

        # ------------------------------------------------------
        # Current workout state
        # ------------------------------------------------------

        self.current_exercise = None
        self.current_side = None
        self.current_rep = 0

        # Last meaningful form feedback
        self.last_feedback = None

        # Prevent repeated "waiting" announcements
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
        """
        Process one normalized workout result.

        Returns:
            list[dict]: speech events generated for this result.
        """

        if not isinstance(result, dict):
            return []

        events = []

        # ------------------------------------------------------
        # Read result safely
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

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # ------------------------------------------------------
        # Safe repetitions
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

        if (
            status in {
                "waiting",
                "waiting_for_exercise",
            }
            and exercise is None
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

            # --------------------------------------------------
            # Ask VoiceCoach for intelligent start message
            # --------------------------------------------------

            coached_message = (
                self.coach.on_exercise_started(
                    active_exercise
                )
            )

            event = exercise_started(
                active_exercise,
                confidence=confidence,
                side=side,
            )

            # Use coached message when available
            if coached_message is not None:

                event["message"] = (
                    coached_message
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

        elif (
            active_exercise
            != self.current_exercise
        ):

            # --------------------------------------------------
            # Ask VoiceCoach for transition message
            # --------------------------------------------------

            coached_message = (
                self.coach.on_exercise_changed(
                    active_exercise
                )
            )

            event = exercise_changed(
                active_exercise,
                confidence=confidence,
                side=side,
            )

            # Use coached message when available
            if coached_message is not None:

                event["message"] = (
                    coached_message
                )

            self.queue.put(event)

            events.append(event)

            self.current_exercise = (
                active_exercise
            )

            self.current_side = side

            # New exercise starts from zero.
            self.current_rep = 0

            self.last_feedback = None

        # ======================================================
        # SAME EXERCISE
        # ======================================================

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

                # --------------------------------------------------
                # IMPORTANT:
                # Get intelligent coaching message from VoiceCoach.
                #
                # Previously the controller only generated:
                #     "Rep 1"
                #
                # Now the actual coach is asked to generate
                # the contextual spoken message.
                # --------------------------------------------------

                coached_message = (
                    self.coach.on_rep_completed(
                        active_exercise,
                        rep_number,
                    )
                )

                # Keep the existing event architecture.
                event = rep_completed(
                    active_exercise,
                    rep_number,
                )

                # --------------------------------------------------
                # Replace generic message with coached message
                # when VoiceCoach provides one.
                # --------------------------------------------------

                if coached_message is not None:

                    event["message"] = (
                        coached_message
                    )

                # --------------------------------------------------
                # Debug logging
                # --------------------------------------------------

                if self.debug:

                    print(
                        f"[VOICE DEBUG] workout event: "
                        f"{event['type']} "
                        f"rep={event['rep']} "
                        f"message={event['message']}"
                    )

                # --------------------------------------------------
                # Send event to asynchronous speech queue
                # --------------------------------------------------

                self.queue.put(event)

                if self.debug:

                    print(
                        f"[VOICE DEBUG] controller received: "
                        f"{event['type']} "
                        f"queued={event['message']}"
                    )

                events.append(event)

            # --------------------------------------------------
            # Update controller state only after all new reps
            # have been processed.
            # --------------------------------------------------

            self.current_rep = reps

        # ======================================================
        # FORM FEEDBACK
        # ======================================================

        feedback = (
            self._normalize_feedback(
                form
            )
        )

        if feedback is not None:

            event = self._announce_feedback(
                feedback
            )

            if event is not None:
                events.append(event)

        # ------------------------------------------------------
        # We are no longer waiting.
        # ------------------------------------------------------

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
    # FEEDBACK ANNOUNCEMENT
    # ==========================================================

    def _announce_feedback(self, message):

        if message == self.last_feedback:
            return None

        # ------------------------------------------------------
        # Ask VoiceCoach to soften/contextualize the feedback.
        # ------------------------------------------------------

        coached_message = (
            self.coach.on_form_feedback(
                message
            )
        )

        event = feedback_message(
            message
        )

        # Use coached message when available.
        if coached_message is not None:

            event["message"] = (
                coached_message
            )

        self.queue.put(event)

        self.last_feedback = message

        return event

    # ==========================================================
    # WAITING ANNOUNCEMENT
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

        # Reset VoiceCoach state too when supported.
        if hasattr(self.coach, "reset"):

            self.coach.reset()

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