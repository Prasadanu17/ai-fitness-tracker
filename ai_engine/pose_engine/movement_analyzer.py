"""
Movement Analyzer

Tracks body movement between frames.

This is intentionally lightweight and does not determine
which exercise is being performed.
"""

import math

from ai_engine.pose_engine.landmark_validator import (
    LandmarkValidator,
)
from ai_engine.pose_engine.pose_types import MovementResult


class MovementAnalyzer:
    """
    Detects meaningful body movement between frames.
    """

    TRACKED_LANDMARKS = (
        11,  # left shoulder
        12,  # right shoulder
        15,  # left wrist
        16,  # right wrist
        23,  # left hip
        24,  # right hip
        25,  # left knee
        26,  # right knee
        27,  # left ankle
        28,  # right ankle
    )

    MOVEMENT_THRESHOLD = 0.012

    def __init__(self):
        self.previous = None

    @staticmethod
    def _distance(a, b):
        dx = float(a.x) - float(b.x)
        dy = float(a.y) - float(b.y)

        return math.sqrt(
            dx * dx + dy * dy
        )

    def analyze(self, landmarks) -> MovementResult:
        """
        Compare current landmarks against previous frame.
        """

        if landmarks is None:
            self.previous = None
            return MovementResult()

        if not self.TRACKED_LANDMARKS:
            return MovementResult()

        valid_indexes = []

        for index in self.TRACKED_LANDMARKS:

            if index >= len(landmarks):
                continue

            if LandmarkValidator.is_valid(
                landmarks[index]
            ):
                valid_indexes.append(index)

        if not valid_indexes:
            self.previous = None
            return MovementResult()

        if self.previous is None:

            self.previous = {
                index: landmarks[index]
                for index in valid_indexes
            }

            return MovementResult(
                is_moving=False,
                movement_score=0.0,
            )

        total_movement = 0.0
        compared = 0

        for index in valid_indexes:

            if index not in self.previous:
                continue

            current = landmarks[index]
            previous = self.previous[index]

            total_movement += self._distance(
                current,
                previous,
            )

            compared += 1

        self.previous = {
            index: landmarks[index]
            for index in valid_indexes
        }

        if compared == 0:
            return MovementResult()

        average_movement = (
            total_movement / compared
        )

        # Normalize into a convenient 0-1 range.
        score = min(
            1.0,
            average_movement / 0.08,
        )

        return MovementResult(
            is_moving=(
                average_movement
                >= self.MOVEMENT_THRESHOLD
            ),
            movement_score=round(
                score,
                3,
            ),
        )

    def reset(self):
        """
        Reset frame history.
        """

        self.previous = None