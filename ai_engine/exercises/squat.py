from ai_engine.angle_calculator import AngleCalculator
from ai_engine.rep_counter import RepCounter


class SquatAnalyzer:
    """
    Squat Analyzer

    Uses MediaPipe pose landmarks.

    Squat knee angle:

        HIP -> KNEE -> ANKLE

    Supported sides:
        left
        right

    Rep cycle:

        UP -> DOWN -> UP
    """

    # MediaPipe Pose landmark indexes
    LEFT_HIP = 23
    RIGHT_HIP = 24

    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(
        self,
        side="right",
        down_threshold=130,
        up_threshold=150,
        smoothing_window=3,
        min_rep_gap=3,
    ):
        self.side = side.lower()

        if self.side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")

        self.down_threshold = down_threshold
        self.up_threshold = up_threshold

        self.rep_counter = RepCounter(
            up_threshold=up_threshold,
            down_threshold=down_threshold,
            smoothing_window=smoothing_window,
            min_rep_gap=min_rep_gap,
        )

        self.last_angle = None
        self.last_state = "UP"
        self.form_feedback = "Ready"

    # ==========================================================
    # LANDMARK SELECTION
    # ==========================================================

    def _get_landmarks(self, landmarks):
        """
        Extract hip, knee and ankle landmarks for the selected side.

        Accepts either:
            - list of landmarks
            - MediaPipe landmark collection
            - result.pose_landmarks[0]
        """

        if self.side == "right":
            hip_index = self.RIGHT_HIP
            knee_index = self.RIGHT_KNEE
            ankle_index = self.RIGHT_ANKLE
        else:
            hip_index = self.LEFT_HIP
            knee_index = self.LEFT_KNEE
            ankle_index = self.LEFT_ANKLE

        hip = landmarks[hip_index]
        knee = landmarks[knee_index]
        ankle = landmarks[ankle_index]

        return hip, knee, ankle

    # ==========================================================
    # ANALYZE
    # ==========================================================

    def analyze(self, landmarks):
        """
        Analyze one frame of MediaPipe pose landmarks.

        Parameters
        ----------
        landmarks:
            MediaPipe pose landmarks.

        Returns
        -------
        dict:
            Squat analysis result.
        """

        hip, knee, ankle = self._get_landmarks(landmarks)

        # Calculate knee angle.
        angle = AngleCalculator.calculate_angle(
            hip,
            knee,
            ankle,
        )

        self.last_angle = float(angle)

        # Update repetition counter.
        result = self.rep_counter.update(angle)

        self.last_state = result["state"]

        # ======================================================
        # FORM FEEDBACK
        # ======================================================

        if angle <= self.down_threshold:

            self.form_feedback = "Squat depth reached"

        elif self.last_state == "DOWN":

            self.form_feedback = "Drive up"

        elif angle >= self.up_threshold:

            self.form_feedback = "Standing position"

        else:

            self.form_feedback = "Moving"

        return self.get_result()

    # ==========================================================
    # GET RESULT
    # ==========================================================

    def get_result(self):
        """
        Return latest squat analysis result.
        """

        return {
            "exercise": "squat",
            "side": self.side,
            "angle": (
                round(self.last_angle, 1)
                if self.last_angle is not None
                else 0.0
            ),
            "reps": self.rep_counter.get_reps(),
            "state": self.last_state,
            "form": self.form_feedback,
        }

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_reps(self):
        return self.rep_counter.get_reps()

    def get_state(self):
        return self.rep_counter.get_state()

    def get_angle(self):
        return self.last_angle

    def get_form_feedback(self):
        return self.form_feedback

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        self.rep_counter.reset()

        self.last_angle = None
        self.last_state = "UP"
        self.form_feedback = "Ready"