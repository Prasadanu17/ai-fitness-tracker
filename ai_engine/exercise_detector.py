"""
Exercise Detector

Automatically determines which supported exercise the
person is currently performing.

Detection strategy:
    Rule-based landmark geometry.

Supported exercises:
    - squat
    - bicep_curl
    - lunge

This module is intentionally independent from the exercise
analyzers. A future ML classifier can replace the detection
logic without changing the rest of the application.
"""

from ai_engine.angle_calculator import AngleCalculator


class ExerciseDetector:
    """
    Detect the current exercise from MediaPipe pose landmarks.
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

    REQUIRED_LANDMARK_COUNT = 29

    # ==========================================================
    # VISIBILITY
    # ==========================================================

    MIN_VISIBILITY = 0.35

    # ==========================================================
    # BICEP CURL
    # ==========================================================

    BICEP_CURL_THRESHOLD = 120

    # ==========================================================
    # LEGS
    # ==========================================================

    LEG_BENT_THRESHOLD = 130

    # Difference between two knee angles.
    #
    # Small difference:
    #     both legs behave similarly -> squat
    #
    # Large difference:
    #     one leg is significantly more bent -> lunge
    #
    LEG_ANGLE_DIFFERENCE = 25

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self):
        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

    # ==========================================================
    # LANDMARK VALIDATION
    # ==========================================================

    @staticmethod
    def _is_valid_landmark(landmark):
        """
        Check whether a MediaPipe landmark contains usable
        coordinates.
        """

        if landmark is None:
            return False

        if not hasattr(landmark, "x"):
            return False

        if not hasattr(landmark, "y"):
            return False

        try:
            x = float(landmark.x)
            y = float(landmark.y)
        except (TypeError, ValueError):
            return False

        # MediaPipe normalized coordinates normally fall
        # between 0 and 1. We allow a small practical range
        # around that to tolerate tracking variations.
        if not (-1.0 <= x <= 2.0):
            return False

        if not (-1.0 <= y <= 2.0):
            return False

        # Test landmarks may not have visibility.
        # If visibility exists, validate it.
        if hasattr(landmark, "visibility"):
            try:
                visibility = float(landmark.visibility)

                if visibility < ExerciseDetector.MIN_VISIBILITY:
                    return False

            except (TypeError, ValueError):
                return False

        return True

    @staticmethod
    def _distance(point_a, point_b):
        """
        Calculate 2D distance between two landmarks.
        """

        dx = float(point_a.x) - float(point_b.x)
        dy = float(point_a.y) - float(point_b.y)

        return (dx * dx + dy * dy) ** 0.5

    def _has_valid_landmarks(self, landmarks, indexes):
        """
        Verify that all requested landmarks are valid.
        """

        if landmarks is None:
            return False

        if len(landmarks) <= max(indexes):
            return False

        for index in indexes:
            if not self._is_valid_landmark(landmarks[index]):
                return False

        return True

    def _has_valid_pose(self, landmarks):
        """
        Check whether the supplied landmarks represent a
        meaningful body pose.

        This prevents dummy test data such as:

            33 landmarks all at (0, 0)

        from being incorrectly detected as bicep curls,
        squats, or lunges.
        """

        if landmarks is None:
            return False

        if len(landmarks) < self.REQUIRED_LANDMARK_COUNT:
            return False

        required_indexes = (
            self.LEFT_SHOULDER,
            self.RIGHT_SHOULDER,
            self.LEFT_ELBOW,
            self.RIGHT_ELBOW,
            self.LEFT_WRIST,
            self.RIGHT_WRIST,
            self.LEFT_HIP,
            self.RIGHT_HIP,
            self.LEFT_KNEE,
            self.RIGHT_KNEE,
            self.LEFT_ANKLE,
            self.RIGHT_ANKLE,
        )

        if not self._has_valid_landmarks(
            landmarks,
            required_indexes,
        ):
            return False

        # ------------------------------------------------------
        # Reject collapsed / identical body points.
        # ------------------------------------------------------

        body_pairs = (
            (
                self.RIGHT_SHOULDER,
                self.RIGHT_ELBOW,
            ),
            (
                self.RIGHT_ELBOW,
                self.RIGHT_WRIST,
            ),
            (
                self.RIGHT_HIP,
                self.RIGHT_KNEE,
            ),
            (
                self.RIGHT_KNEE,
                self.RIGHT_ANKLE,
            ),
            (
                self.LEFT_SHOULDER,
                self.LEFT_ELBOW,
            ),
            (
                self.LEFT_ELBOW,
                self.LEFT_WRIST,
            ),
            (
                self.LEFT_HIP,
                self.LEFT_KNEE,
            ),
            (
                self.LEFT_KNEE,
                self.LEFT_ANKLE,
            ),
        )

        for index_a, index_b in body_pairs:

            point_a = landmarks[index_a]
            point_b = landmarks[index_b]

            if self._distance(point_a, point_b) < 0.001:
                return False

        return True

    # ==========================================================
    # ANGLE HELPER
    # ==========================================================

    @staticmethod
    def _calculate_angle(point_a, point_b, point_c):
        """
        Calculate angle A-B-C.
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
        """
        Detect bicep curl using elbow angles.

        The side with the smallest elbow angle is selected.
        """

        candidates = []

        # ------------------------------------------------------
        # RIGHT ARM
        # ------------------------------------------------------

        right_indexes = (
            self.RIGHT_SHOULDER,
            self.RIGHT_ELBOW,
            self.RIGHT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):

            right_angle = self._calculate_angle(
                landmarks[self.RIGHT_SHOULDER],
                landmarks[self.RIGHT_ELBOW],
                landmarks[self.RIGHT_WRIST],
            )

            candidates.append(
                ("right", right_angle)
            )

        # ------------------------------------------------------
        # LEFT ARM
        # ------------------------------------------------------

        left_indexes = (
            self.LEFT_SHOULDER,
            self.LEFT_ELBOW,
            self.LEFT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):

            left_angle = self._calculate_angle(
                landmarks[self.LEFT_SHOULDER],
                landmarks[self.LEFT_ELBOW],
                landmarks[self.LEFT_WRIST],
            )

            candidates.append(
                ("left", left_angle)
            )

        if not candidates:
            return None, 0.0, None

        # ------------------------------------------------------
        # Choose the most contracted arm.
        # ------------------------------------------------------

        side, angle = min(
            candidates,
            key=lambda item: item[1],
        )

        # ------------------------------------------------------
        # Determine whether it is actually a curl.
        # ------------------------------------------------------

        if angle <= self.BICEP_CURL_THRESHOLD:

            confidence = min(
                0.98,
                0.70
                + (
                    (
                        self.BICEP_CURL_THRESHOLD
                        - angle
                    )
                    / self.BICEP_CURL_THRESHOLD
                )
                * 0.25,
            )

            return (
                "bicep_curl",
                round(confidence, 2),
                side,
            )

        return None, 0.0, None

    # ==========================================================
    # LEG ANGLES
    # ==========================================================

    def _get_leg_angles(self, landmarks):
        """
        Return:

            right_knee_angle,
            left_knee_angle
        """

        right_indexes = (
            self.RIGHT_HIP,
            self.RIGHT_KNEE,
            self.RIGHT_ANKLE,
        )

        left_indexes = (
            self.LEFT_HIP,
            self.LEFT_KNEE,
            self.LEFT_ANKLE,
        )

        right_angle = None
        left_angle = None

        # ------------------------------------------------------
        # RIGHT LEG
        # ------------------------------------------------------

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):

            right_angle = self._calculate_angle(
                landmarks[self.RIGHT_HIP],
                landmarks[self.RIGHT_KNEE],
                landmarks[self.RIGHT_ANKLE],
            )

        # ------------------------------------------------------
        # LEFT LEG
        # ------------------------------------------------------

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):

            left_angle = self._calculate_angle(
                landmarks[self.LEFT_HIP],
                landmarks[self.LEFT_KNEE],
                landmarks[self.LEFT_ANKLE],
            )

        return right_angle, left_angle

    # ==========================================================
    # SQUAT / LUNGE DETECTION
    # ==========================================================

    def _detect_leg_exercise(self, landmarks):
        """
        Distinguish squat from lunge.

        Squat:
            Both knees bend similarly.

        Lunge:
            One knee bends significantly more than
            the other.
        """

        right_angle, left_angle = self._get_leg_angles(
            landmarks
        )

        if (
            right_angle is None
            and left_angle is None
        ):
            return None, 0.0, None

        # ======================================================
        # BOTH LEGS AVAILABLE
        # ======================================================

        if (
            right_angle is not None
            and left_angle is not None
        ):

            right_bent = (
                right_angle <= self.LEG_BENT_THRESHOLD
            )

            left_bent = (
                left_angle <= self.LEG_BENT_THRESHOLD
            )

            angle_difference = abs(
                right_angle - left_angle
            )

            # --------------------------------------------------
            # SQUAT
            # --------------------------------------------------

            if (
                right_bent
                and left_bent
                and angle_difference
                <= self.LEG_ANGLE_DIFFERENCE
            ):

                confidence = 0.85

                # Deeper and symmetrical squat.
                if (
                    right_angle <= 100
                    and left_angle <= 100
                ):
                    confidence = 0.92

                return (
                    "squat",
                    confidence,
                    "right",
                )

            # --------------------------------------------------
            # RIGHT LEG LUNGE
            # --------------------------------------------------

            if (
                right_bent
                and (
                    not left_bent
                    or angle_difference
                    > self.LEG_ANGLE_DIFFERENCE
                )
            ):

                return (
                    "lunge",
                    0.82,
                    "right",
                )

            # --------------------------------------------------
            # LEFT LEG LUNGE
            # --------------------------------------------------

            if (
                left_bent
                and (
                    not right_bent
                    or angle_difference
                    > self.LEG_ANGLE_DIFFERENCE
                )
            ):

                return (
                    "lunge",
                    0.82,
                    "left",
                )

        # ======================================================
        # ONLY RIGHT LEG AVAILABLE
        # ======================================================

        if right_angle is not None:

            if right_angle <= self.LEG_BENT_THRESHOLD:

                return (
                    "lunge",
                    0.65,
                    "right",
                )

        # ======================================================
        # ONLY LEFT LEG AVAILABLE
        # ======================================================

        if left_angle is not None:

            if left_angle <= self.LEG_BENT_THRESHOLD:

                return (
                    "lunge",
                    0.65,
                    "left",
                )

        return None, 0.0, None

    # ==========================================================
    # MAIN DETECTION
    # ==========================================================

    def detect(self, landmarks):
        """
        Detect exercise from one pose frame.

        Returns:

            {
                "exercise": "squat",
                "confidence": 0.85,
                "side": "right"
            }

        If no reliable exercise is detected:

            {
                "exercise": None,
                "confidence": 0.0,
                "side": None
            }
        """

        # ------------------------------------------------------
        # No landmarks.
        # ------------------------------------------------------

        if landmarks is None:
            return self._empty_result()

        # ------------------------------------------------------
        # Basic collection validation.
        # ------------------------------------------------------

        try:
            landmark_count = len(landmarks)
        except TypeError:
            return self._empty_result()

        if landmark_count < self.REQUIRED_LANDMARK_COUNT:
            return self._empty_result()

        # ------------------------------------------------------
        # Validate actual pose geometry.
        # ------------------------------------------------------

        if not self._has_valid_pose(landmarks):
            return self._empty_result()

        # ------------------------------------------------------
        # Check bicep curl first.
        # ------------------------------------------------------

        exercise, confidence, side = (
            self._detect_bicep_curl(landmarks)
        )

        if exercise is not None:

            return self._set_result(
                exercise,
                confidence,
                side,
            )

        # ------------------------------------------------------
        # Check squat / lunge.
        # ------------------------------------------------------

        exercise, confidence, side = (
            self._detect_leg_exercise(landmarks)
        )

        if exercise is not None:

            return self._set_result(
                exercise,
                confidence,
                side,
            )

        # ------------------------------------------------------
        # Nothing detected.
        # ------------------------------------------------------

        return self._empty_result()

    # ==========================================================
    # RESULT HELPERS
    # ==========================================================

    def _set_result(
        self,
        exercise,
        confidence,
        side,
    ):
        """
        Store and return a detection result.
        """

        self.current_exercise = exercise
        self.current_confidence = float(confidence)
        self.current_side = side

        return {
            "exercise": exercise,
            "confidence": float(confidence),
            "side": side,
        }

    def _empty_result(self):
        """
        Clear the current detection and return an empty result.
        """

        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        return {
            "exercise": None,
            "confidence": 0.0,
            "side": None,
        }

    # ==========================================================
    # GETTERS
    # ==========================================================

    def get_current_exercise(self):
        """
        Return the currently detected exercise.
        """

        return self.current_exercise

    def get_confidence(self):
        """
        Return the current detection confidence.
        """

        return self.current_confidence

    def get_current_side(self):
        """
        Return the currently detected side.
        """

        return self.current_side

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):
        """
        Reset detector state.
        """

        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None