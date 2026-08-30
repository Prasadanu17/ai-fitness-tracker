"""
Pose Quality

Calculates how trustworthy the current body tracking is.
"""

from ai_engine.pose_engine.landmark_validator import (
    LandmarkValidator,
)
from ai_engine.pose_engine.pose_types import PoseQuality


class PoseQualityAnalyzer:
    """
    Calculates pose tracking quality.
    """

    IMPORTANT_LANDMARKS = (
        11, 12,  # shoulders
        13, 14,  # elbows
        15, 16,  # wrists
        23, 24,  # hips
        25, 26,  # knees
        27, 28,  # ankles
    )

    def analyze(self, landmarks) -> PoseQuality:
        """
        Analyze landmark quality.
        """

        if landmarks is None:
            return PoseQuality()

        valid_count = LandmarkValidator.count_valid(
            landmarks
        )

        important_valid = 0

        for index in self.IMPORTANT_LANDMARKS:

            if index >= len(landmarks):
                continue

            if LandmarkValidator.is_valid(
                landmarks[index]
            ):
                important_valid += 1

        total_important = len(self.IMPORTANT_LANDMARKS)

        if total_important == 0:
            return PoseQuality()

        important_score = (
            important_valid / total_important
        )

        overall_score = (
            valid_count / max(len(landmarks), 1)
        )

        # Important body joints matter more than
        # miscellaneous landmarks.
        score = (
            important_score * 0.75
            + overall_score * 0.25
        )

        score = max(
            0.0,
            min(1.0, score),
        )

        return PoseQuality(
            score=round(score, 3),
            visible_landmarks=valid_count,
            required_landmarks=total_important,
            is_valid=score >= 0.55,
        )