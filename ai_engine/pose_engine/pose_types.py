"""
Pose Types

Shared constants and lightweight data structures used by
the pose-processing layer.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PoseState(str, Enum):
    """
    General body position.
    """

    UNKNOWN = "unknown"
    STANDING = "standing"
    SITTING = "sitting"
    MOVING = "moving"
    STILL = "still"


@dataclass
class PoseQuality:
    """
    Describes how reliable the current pose landmarks are.
    """

    score: float = 0.0
    visible_landmarks: int = 0
    required_landmarks: int = 0
    is_valid: bool = False

    @property
    def percentage(self) -> float:
        return round(self.score * 100.0, 1)


@dataclass
class PoseStateResult:
    """
    Result returned by PoseStateDetector.
    """

    state: PoseState = PoseState.UNKNOWN
    confidence: float = 0.0
    is_sitting: bool = False
    is_standing: bool = False


@dataclass
class MovementResult:
    """
    Result returned by MovementAnalyzer.
    """

    is_moving: bool = False
    movement_score: float = 0.0
    direction: Optional[str] = None