"""
Detection Stabilizer

Stabilizes exercise detection across multiple frames.

Purpose:
    Prevent a single noisy frame from immediately changing
    the detected exercise.

Example:

    squat
    squat
    bicep_curl   <- noise
    squat

The stabilizer keeps the confirmed exercise as squat.

An exercise is confirmed only after it has been detected
consistently for a configurable number of frames.
"""


class DetectionStabilizer:
    """
    Stabilize exercise detection over consecutive frames.
    """

    def __init__(
        self,
        confirmation_frames=3,
        minimum_confidence=0.60,
    ):
        self.confirmation_frames = max(
            1,
            int(confirmation_frames),
        )

        self.minimum_confidence = float(
            minimum_confidence
        )

        self.current_exercise = None
        self.current_side = None
        self.current_confidence = 0.0

        self.candidate_exercise = None
        self.candidate_side = None
        self.candidate_confidence = 0.0
        self.candidate_frames = 0

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update(
        self,
        exercise,
        confidence,
        side=None,
    ):
        """
        Process one exercise detection.

        Parameters
        ----------
        exercise : str or None
            Detected exercise.

        confidence : float
            Detection confidence.

        side : str or None
            Detected body side.

        Returns
        -------
        dict
            Stabilized detection result.
        """

        confidence = float(confidence)

        # ------------------------------------------------------
        # Invalid / low-confidence detection
        # ------------------------------------------------------

        if (
            exercise is None
            or confidence < self.minimum_confidence
        ):
            self._reset_candidate()

            return self._build_result(
                detected_exercise=None,
                detected_side=None,
                detected_confidence=confidence,
                status="waiting",
            )

        exercise = str(exercise).strip().lower()

        # ------------------------------------------------------
        # Same candidate
        # ------------------------------------------------------

        if (
            self.candidate_exercise == exercise
            and self.candidate_side == side
        ):
            self.candidate_frames += 1

            # Keep the strongest confidence observed.
            self.candidate_confidence = max(
                self.candidate_confidence,
                confidence,
            )

        # ------------------------------------------------------
        # New candidate
        # ------------------------------------------------------

        else:
            self.candidate_exercise = exercise
            self.candidate_side = side
            self.candidate_confidence = confidence
            self.candidate_frames = 1

        # ------------------------------------------------------
        # Confirm candidate
        # ------------------------------------------------------

        if (
            self.candidate_frames
            >= self.confirmation_frames
        ):
            self.current_exercise = (
                self.candidate_exercise
            )

            self.current_side = (
                self.candidate_side
            )

            self.current_confidence = (
                self.candidate_confidence
            )

            return self._build_result(
                detected_exercise=exercise,
                detected_side=side,
                detected_confidence=confidence,
                status="confirmed",
            )

        # ------------------------------------------------------
        # Candidate still being confirmed
        # ------------------------------------------------------

        return self._build_result(
            detected_exercise=exercise,
            detected_side=side,
            detected_confidence=confidence,
            status="detecting",
        )

    # ==========================================================
    # RESULT
    # ==========================================================

    def _build_result(
        self,
        detected_exercise,
        detected_side,
        detected_confidence,
        status,
    ):
        """
        Build a standardized result.
        """

        return {
            "exercise": self.current_exercise,
            "confidence": self.current_confidence,
            "side": self.current_side,

            "detected_exercise": detected_exercise,
            "detected_confidence": detected_confidence,
            "detected_side": detected_side,

            "candidate_exercise": (
                self.candidate_exercise
            ),

            "candidate_side": (
                self.candidate_side
            ),

            "candidate_frames": (
                self.candidate_frames
            ),

            "status": status,
        }

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_current_exercise(self):
        """
        Return the currently confirmed exercise.
        """

        return self.current_exercise

    def get_current_side(self):
        """
        Return the currently confirmed side.
        """

        return self.current_side

    def get_confidence(self):
        """
        Return confidence of the confirmed exercise.
        """

        return self.current_confidence

    def get_candidate_exercise(self):
        """
        Return the exercise currently being evaluated.
        """

        return self.candidate_exercise

    def get_candidate_frames(self):
        """
        Return the number of consecutive candidate frames.
        """

        return self.candidate_frames

    # ==========================================================
    # RESET CANDIDATE
    # ==========================================================

    def _reset_candidate(self):
        """
        Clear the current candidate without removing the
        confirmed exercise.
        """

        self.candidate_exercise = None
        self.candidate_side = None
        self.candidate_confidence = 0.0
        self.candidate_frames = 0

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Completely reset the stabilizer.
        """

        self.current_exercise = None
        self.current_side = None
        self.current_confidence = 0.0

        self._reset_candidate()

    # ==========================================================
    # STATUS
    # ==========================================================

    def is_confirmed(self):
        """
        Return whether an exercise is currently confirmed.
        """

        return self.current_exercise is not None