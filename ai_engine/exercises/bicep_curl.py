from ai_engine.exercises.base_exercise_analyzer import BaseExerciseAnalyzer
from ai_engine.analysis.angle_calculator import AngleCalculator
from ai_engine.analysis.rep_counter import RepCounter


class BicepCurlAnalyzer(BaseExerciseAnalyzer):
    """
    Bicep Curl Analyzer

    Uses MediaPipe pose landmarks.

    Bicep curl elbow angle:

        SHOULDER -> ELBOW -> WRIST

    Supported sides:
        left
        right

    Rep cycle:

        EXTENDED -> CONTRACTED -> EXTENDED
    """

    exercise_name = "bicep_curl"

    # ==========================================================
    # MEDIAPIPE LANDMARK INDEXES
    # ==========================================================

    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        side="right",
        down_threshold=60,
        up_threshold=160,
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
        Extract shoulder, elbow and wrist landmarks
        for the selected side.
        """

        if self.side == "right":
            shoulder_index = self.RIGHT_SHOULDER
            elbow_index = self.RIGHT_ELBOW
            wrist_index = self.RIGHT_WRIST
        else:
            shoulder_index = self.LEFT_SHOULDER
            elbow_index = self.LEFT_ELBOW
            wrist_index = self.LEFT_WRIST

        shoulder = landmarks[shoulder_index]
        elbow = landmarks[elbow_index]
        wrist = landmarks[wrist_index]

        return shoulder, elbow, wrist

    # ==========================================================
    # ANALYZE
    # ==========================================================

    def analyze(self, landmarks):
        """
        Analyze one frame of MediaPipe pose landmarks.

        Returns:
            dict containing the current bicep curl analysis.
        """

        shoulder, elbow, wrist = self._get_landmarks(landmarks)

        # Calculate elbow angle.
        angle = AngleCalculator.calculate_angle(
            shoulder,
            elbow,
            wrist,
        )

        self.last_angle = float(angle)

        # Update repetition counter.
        result = self.rep_counter.update(angle)

        self.last_state = result["state"]

        # Update form feedback.
        self.form_feedback = self._get_form_status()

        return self.get_result()

    # ==========================================================
    # FORM ANALYSIS
    # ==========================================================

    def _get_form_status(self):
        """
        Basic bicep curl movement feedback.
        """

        if self.last_angle is None:
            return "Ready"

        if self.last_angle <= self.down_threshold:
            return "Arm contracted"

        if self.last_state == "DOWN":
            return "Lowering arm"

        if self.last_angle >= self.up_threshold:
            return "Arm extended"

        return "Moving"

    # ==========================================================
    # RESULT
    # ==========================================================

    def get_result(self):
        """
        Return the latest bicep curl analysis result.
        """

        return {
            "exercise": self.exercise_name,
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
        """
        Reset the analyzer to its initial state.
        """

        self.rep_counter.reset()

        self.last_angle = None
        self.last_state = "UP"
        self.form_feedback = "Ready"