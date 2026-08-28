from ai_engine.angle_calculator import AngleCalculator
from ai_engine.rep_counter import RepCounter


class BicepCurlAnalyzer:
    """
    Analyzes bicep curl movement using the elbow angle.
    """

    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15

    def __init__(self, side="right"):
        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")

        self.side = side

        self.rep_counter = RepCounter(
            up_threshold=160,
            down_threshold=60
        )

        self.angle = 0.0

    def analyze(self, landmarks):
        """
        Analyze one frame of pose landmarks.

        Returns:
            dict with angle, reps, state and form status.
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

        self.angle = AngleCalculator.calculate_angle(
            shoulder,
            elbow,
            wrist
        )

        reps = self.rep_counter.update(self.angle)
        state = self.rep_counter.get_state()

        return {
            "exercise": "bicep_curl",
            "side": self.side,
            "angle": round(self.angle, 1),
            "reps": reps,
            "state": state,
            "form": self._get_form_status()
        }

    def _get_form_status(self):
        if self.angle >= 160:
            return "Arm extended"

        if self.angle <= 60:
            return "Arm contracted"

        return "Moving"

    def get_result(self):
        return {
            "exercise": "bicep_curl",
            "side": self.side,
            "angle": round(self.angle, 1),
            "reps": self.rep_counter.get_reps(),
            "state": self.rep_counter.get_state(),
            "form": self._get_form_status()
        }

    def reset(self):
        self.angle = 0.0
        self.rep_counter.reset()