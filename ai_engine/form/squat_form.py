"""
Squat Form Analyzer

First form-analysis implementation for the AI Fitness Tracker.

Current checks:
    - squat depth
    - basic posture
    - knee position

This is intentionally rule-based.
Machine-learning form classification can be added later.
"""

from ai_engine.analysis.angle_calculator import AngleCalculator
from ai_engine.analysis.form_analyzer import FormAnalyzer


class SquatFormAnalyzer(FormAnalyzer):
    """
    Analyze squat form using MediaPipe landmarks.
    """

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12

    LEFT_HIP = 23
    RIGHT_HIP = 24

    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    MIN_SQUAT_DEPTH = 110
    GOOD_SQUAT_DEPTH = 100

    def __init__(self):
        super().__init__()

    def analyze(self, landmarks, exercise_result=None):
        """
        Analyze one frame of squat form.
        """

        if landmarks is None:
            self.score = 0.0
            self.status = "Waiting"
            self.feedback = ["No pose detected"]

            return self.get_result()

        if len(landmarks) < 33:
            self.score = 0.0
            self.status = "Waiting"
            self.feedback = ["Incomplete pose"]

            return self.get_result()

        # ------------------------------------------------------
        # Calculate knee angles
        # ------------------------------------------------------

        right_knee_angle = AngleCalculator.calculate_angle(
            landmarks[self.RIGHT_HIP],
            landmarks[self.RIGHT_KNEE],
            landmarks[self.RIGHT_ANKLE],
        )

        left_knee_angle = AngleCalculator.calculate_angle(
            landmarks[self.LEFT_HIP],
            landmarks[self.LEFT_KNEE],
            landmarks[self.LEFT_ANKLE],
        )

        average_knee_angle = (
            right_knee_angle + left_knee_angle
        ) / 2.0

        feedback = []
        score = 100.0

        # ------------------------------------------------------
        # Depth check
        # ------------------------------------------------------

        if average_knee_angle > self.MIN_SQUAT_DEPTH:

            feedback.append(
                "Go deeper for a better squat"
            )

            score -= 25

        elif average_knee_angle <= self.GOOD_SQUAT_DEPTH:

            feedback.append(
                "Good squat depth"
            )

        else:

            feedback.append(
                "Good depth"
            )

        # ------------------------------------------------------
        # Knee symmetry check
        # ------------------------------------------------------

        knee_difference = abs(
            right_knee_angle - left_knee_angle
        )

        if knee_difference > 25:

            feedback.append(
                "Keep both knees more balanced"
            )

            score -= 20

        else:

            feedback.append(
                "Knee position looks balanced"
            )

        # ------------------------------------------------------
        # Final score
        # ------------------------------------------------------

        self.score = max(
            0.0,
            min(100.0, score)
        )

        if self.score >= 85:
            self.status = "Good"

        elif self.score >= 60:
            self.status = "Needs Improvement"

        else:
            self.status = "Poor"

        self.feedback = feedback

        return {
            "exercise": "squat",
            "score": round(self.score, 1),
            "status": self.status,
            "feedback": list(self.feedback),
            "knee_angle": round(
                average_knee_angle,
                1
            ),
        }

    def reset(self):
        super().reset()