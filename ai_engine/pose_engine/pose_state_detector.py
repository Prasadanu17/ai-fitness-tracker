"""
Pose State Detector

Determines whether the person is generally:

    - standing
    - sitting
    - unknown

This is NOT an exercise detector.

It provides context for exercise detection.
"""

from ai_engine.analysis.angle_calculator import AngleCalculator
from ai_engine.pose_engine.landmark_validator import (
    LandmarkValidator,
)
from ai_engine.pose_engine.pose_types import (
    PoseState,
    PoseStateResult,
)


class PoseStateDetector:
    """
    Detect general body position.
    """

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12

    LEFT_HIP = 23
    RIGHT_HIP = 24

    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    SITTING_KNEE_MAX = 125

    STANDING_KNEE_MIN = 145

    REQUIRED = (
        LEFT_HIP,
        RIGHT_HIP,
        LEFT_KNEE,
        RIGHT_KNEE,
        LEFT_ANKLE,
        RIGHT_ANKLE,
    )

    def _angle(self, a, b, c):
        return AngleCalculator.calculate_angle(
            a,
            b,
            c,
        )

    def detect(self, landmarks) -> PoseStateResult:
        """
        Detect standing/sitting state.
        """

        if not LandmarkValidator.validate(
            landmarks,
            self.REQUIRED,
        ):
            return PoseStateResult()

        right_angle = self._angle(
            landmarks[self.RIGHT_HIP],
            landmarks[self.RIGHT_KNEE],
            landmarks[self.RIGHT_ANKLE],
        )

        left_angle = self._angle(
            landmarks[self.LEFT_HIP],
            landmarks[self.LEFT_KNEE],
            landmarks[self.LEFT_ANKLE],
        )

        average_angle = (
            right_angle + left_angle
        ) / 2.0

        # ------------------------------------------------------
        # SITTING
        # ------------------------------------------------------

        if average_angle <= self.SITTING_KNEE_MAX:

            confidence = min(
                0.98,
                0.70
                + (
                    self.SITTING_KNEE_MAX
                    - average_angle
                ) / 100.0,
            )

            return PoseStateResult(
                state=PoseState.SITTING,
                confidence=round(confidence, 2),
                is_sitting=True,
                is_standing=False,
            )

        # ------------------------------------------------------
        # STANDING
        # ------------------------------------------------------

        if average_angle >= self.STANDING_KNEE_MIN:

            confidence = min(
                0.98,
                0.70
                + (
                    average_angle
                    - self.STANDING_KNEE_MIN
                ) / 100.0,
            )

            return PoseStateResult(
                state=PoseState.STANDING,
                confidence=round(confidence, 2),
                is_sitting=False,
                is_standing=True,
            )

        # ------------------------------------------------------
        # TRANSITION / UNKNOWN
        # ------------------------------------------------------

        return PoseStateResult(
            state=PoseState.UNKNOWN,
            confidence=0.40,
            is_sitting=False,
            is_standing=False,
        )