"""
Exercise Detector

Automatically determines which supported exercise the
person is currently performing.

Current detection strategy:
    Rule-based landmark geometry.

Supported exercises:
    - squat
    - bicep_curl
    - lunge

This is the first automatic-detection layer.
A machine-learning classifier can replace this detector
later without changing the exercise analyzers.
"""

from ai_engine.angle_calculator import AngleCalculator


class ExerciseDetector:
    """
    Detect the current exercise from MediaPipe landmarks.
    """

    # ==========================================================
    # MEDIAPIPE LANDMARK INDEXES
    # ==========================================================

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12

    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14

    LEFT_WRIST = 15
    RIGHT_WRIST = 16

    LEFT_HIP = 23
    RIGHT_HIP = 24

    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    # ==========================================================
    # THRESHOLDS
    # ==========================================================

    # Bicep curl
    BICEP_CURL_THRESHOLD = 120

    # Squat / lunge
    LEG_BENT_THRESHOLD = 130

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):

        self.current_exercise = None

        self.current_confidence = 0.0

    # ==========================================================
    # ANGLE HELPERS
    # ==========================================================

    @staticmethod
    def _calculate_angle(point_a, point_b, point_c):
        """
        Calculate the angle A-B-C.
        """

        return AngleCalculator.calculate_angle(
            point_a,
            point_b,
            point_c,
        )

    # ==========================================================
    # BICEP CURL DETECTION
    # ==========================================================

    def _detect_bicep_curl(self, landmarks):

        right_angle = self._calculate_angle(
            landmarks[self.RIGHT_SHOULDER],
            landmarks[self.RIGHT_ELBOW],
            landmarks[self.RIGHT_WRIST],
        )

        left_angle = self._calculate_angle(
            landmarks[self.LEFT_SHOULDER],
            landmarks[self.LEFT_ELBOW],
            landmarks[self.LEFT_WRIST],
        )

        # A strongly bent elbow is a strong bicep-curl signal.
        if right_angle <= self.BICEP_CURL_THRESHOLD:

            return "bicep_curl", 0.90, "right"

        if left_angle <= self.BICEP_CURL_THRESHOLD:

            return "bicep_curl", 0.90, "left"

        return None, 0.0, None

    # ==========================================================
    # LEG ANGLE DETECTION
    # ==========================================================

    def _get_leg_angles(self, landmarks):

        right_knee_angle = self._calculate_angle(
            landmarks[self.RIGHT_HIP],
            landmarks[self.RIGHT_KNEE],
            landmarks[self.RIGHT_ANKLE],
        )

        left_knee_angle = self._calculate_angle(
            landmarks[self.LEFT_HIP],
            landmarks[self.LEFT_KNEE],
            landmarks[self.LEFT_ANKLE],
        )

        return right_knee_angle, left_knee_angle

    # ==========================================================
    # SQUAT / LUNGE DETECTION
    # ==========================================================

    def _detect_leg_exercise(self, landmarks):

        right_angle, left_angle = self._get_leg_angles(
            landmarks
        )

        right_bent = right_angle <= self.LEG_BENT_THRESHOLD
        left_bent = left_angle <= self.LEG_BENT_THRESHOLD

        # Both legs bent similarly → likely squat.
        if right_bent and left_bent:

            return "squat", 0.85, "right"

        # One leg bent while the other remains relatively
        # extended → likely lunge.
        if right_bent and not left_bent:

            return "lunge", 0.80, "right"

        if left_bent and not right_bent:

            return "lunge", 0.80, "left"

        return None, 0.0, None

    # ==========================================================
    # MAIN DETECTION
    # ==========================================================

    def detect(self, landmarks):

        """
        Detect the exercise from one frame.

        Returns
        -------

        dict:

            {
                "exercise": "squat",
                "confidence": 0.85,
                "side": "right"
            }

        If no exercise can be determined:

            {
                "exercise": None,
                "confidence": 0.0,
                "side": None
            }
        """

        if landmarks is None:

            return {
                "exercise": None,
                "confidence": 0.0,
                "side": None,
            }

        # ------------------------------------------------------
        # First check upper-body movement.
        # ------------------------------------------------------

        exercise, confidence, side = (
            self._detect_bicep_curl(landmarks)
        )

        if exercise is not None:

            self.current_exercise = exercise
            self.current_confidence = confidence

            return {
                "exercise": exercise,
                "confidence": confidence,
                "side": side,
            }

        # ------------------------------------------------------
        # Then check leg movement.
        # ------------------------------------------------------

        exercise, confidence, side = (
            self._detect_leg_exercise(landmarks)
        )

        if exercise is not None:

            self.current_exercise = exercise
            self.current_confidence = confidence

            return {
                "exercise": exercise,
                "confidence": confidence,
                "side": side,
            }

        # ------------------------------------------------------
        # Nothing confidently detected.
        # ------------------------------------------------------

        self.current_exercise = None
        self.current_confidence = 0.0

        return {
            "exercise": None,
            "confidence": 0.0,
            "side": None,
        }

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_current_exercise(self):

        return self.current_exercise

    def get_confidence(self):

        return self.current_confidence

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.current_exercise = None

        self.current_confidence = 0.0