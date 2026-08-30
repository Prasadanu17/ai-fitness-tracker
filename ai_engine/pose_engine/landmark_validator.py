"""
Landmark Validator

Responsible for validating MediaPipe pose landmarks.

This module does NOT decide which exercise the person is doing.
It only answers:

    "Can I trust these landmarks?"
"""

from typing import Iterable


class LandmarkValidator:
    """
    Validates MediaPipe-style pose landmarks.
    """

    MIN_VISIBILITY = 0.35

    MIN_LANDMARK_COUNT = 29

    @classmethod
    def is_valid(cls, landmark) -> bool:
        """
        Validate a single landmark.
        """

        if landmark is None:
            return False

        if not hasattr(landmark, "x") or not hasattr(landmark, "y"):
            return False

        try:
            x = float(landmark.x)
            y = float(landmark.y)
        except (TypeError, ValueError):
            return False

        if not (-1.0 <= x <= 2.0):
            return False

        if not (-1.0 <= y <= 2.0):
            return False

        if hasattr(landmark, "visibility"):
            try:
                visibility = float(landmark.visibility)
            except (TypeError, ValueError):
                return False

            if visibility < cls.MIN_VISIBILITY:
                return False

        return True

    @classmethod
    def count_valid(cls, landmarks) -> int:
        """
        Count usable landmarks.
        """

        if landmarks is None:
            return 0

        return sum(
            1
            for landmark in landmarks
            if cls.is_valid(landmark)
        )

    @classmethod
    def validate(
        cls,
        landmarks,
        required_indexes: Iterable[int] = None,
    ) -> bool:
        """
        Validate a complete landmark collection.

        If required_indexes are supplied, every requested
        landmark must be valid.
        """

        if landmarks is None:
            return False

        try:
            if len(landmarks) < cls.MIN_LANDMARK_COUNT:
                return False
        except TypeError:
            return False

        if required_indexes is None:
            return cls.count_valid(landmarks) >= cls.MIN_LANDMARK_COUNT

        for index in required_indexes:

            if index >= len(landmarks):
                return False

            if not cls.is_valid(landmarks[index]):
                return False

        return True