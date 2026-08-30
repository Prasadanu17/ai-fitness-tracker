"""
Exercise Detector

Stable rule-based exercise detection using MediaPipe landmarks.

Supported exercises:
    - squat
    - bicep_curl
    - lunge

The detector intentionally uses temporal stabilization.

A single noisy frame must NOT immediately change the
currently detected exercise.
"""

from collections import deque

from ai_engine.analysis.angle_calculator import AngleCalculator


class ExerciseDetector:
    """
    Detect and stabilize exercises from MediaPipe landmarks.
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
    # DETECTION THRESHOLDS
    # ==========================================================

    # Bicep curl requires a clearly bent elbow.
    BICEP_CURL_THRESHOLD = 115

    # Straight-arm rejection.
    BICEP_STRAIGHT_THRESHOLD = 145

    # Minimum difference between arm angles.
    # Prevents both arms being equally bent from
    # immediately becoming a curl.
    BICEP_SIDE_ADVANTAGE = 12

    # Knee angle indicating a bent leg.
    LEG_BENT_THRESHOLD = 130

    # Deep squat.
    DEEP_SQUAT_THRESHOLD = 105

    # Difference between knee angles.
    LUNGE_ANGLE_DIFFERENCE = 28

    # ==========================================================
    # TEMPORAL STABILIZATION
    # ==========================================================

    # Number of matching observations required before
    # confirming a new exercise.
    CONFIRMATION_FRAMES = 5

    # Number of recent observations used.
    HISTORY_SIZE = 8

    # Number of matching observations needed to maintain
    # an already active exercise.
    STABLE_MATCHES_REQUIRED = 3

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        confirmation_frames=CONFIRMATION_FRAMES,
        history_size=HISTORY_SIZE,
    ):
        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        self.confirmation_frames = max(
            1,
            int(confirmation_frames),
        )

        self.history_size = max(
            self.confirmation_frames,
            int(history_size),
        )

        self.detection_history = deque(
            maxlen=self.history_size
        )

        self.pending_exercise = None
        self.pending_side = None
        self.pending_count = 0

        self.stable_match_count = 0

    # ==========================================================
    # LANDMARK VALIDATION
    # ==========================================================

    def _is_valid_landmark(self, landmark):
        if landmark is None:
            return False

        required_attrs = ("x", "y", "z")
        for attr in required_attrs:
            if not hasattr(landmark, attr):
                return False

        try:
            x = float(landmark.x)
            y = float(landmark.y)
            z = float(landmark.z)
        except (TypeError, ValueError):
            return False

        if not (-1.0 <= x <= 2.0):
            return False

        if not (-1.0 <= y <= 2.0):
            return False

        if not (-1.0 <= z <= 2.0):
            return False

        if hasattr(landmark, "visibility"):
            try:
                visibility = float(
                    landmark.visibility
                )
            except (TypeError, ValueError):
                return False

            if visibility < self.MIN_VISIBILITY:
                return False

        return True

    @staticmethod
    def _distance(point_a, point_b):
        dx = float(point_a.x) - float(point_b.x)
        dy = float(point_a.y) - float(point_b.y)

        return (dx * dx + dy * dy) ** 0.5

    def _has_valid_landmarks(
        self,
        landmarks,
        indexes,
    ):
        if landmarks is None:
            return False

        try:
            if len(landmarks) <= max(indexes):
                return False
        except (TypeError, ValueError):
            return False

        for index in indexes:

            if not self._is_valid_landmark(
                landmarks[index]
            ):
                return False

        return True

    def _has_valid_pose(self, landmarks):

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

            if self._distance(
                landmarks[index_a],
                landmarks[index_b],
            ) < 0.001:

                return False

        return True

    # ==========================================================
    # ANGLE
    # ==========================================================

    @staticmethod
    def _calculate_angle(
        point_a,
        point_b,
        point_c,
    ):

        return AngleCalculator.calculate_angle(
            point_a,
            point_b,
            point_c,
        )

    # ==========================================================
    # BICEP CURL
    # ==========================================================

    def _get_arm_angles(self, landmarks):

        candidates = []

        right_indexes = (
            self.RIGHT_SHOULDER,
            self.RIGHT_ELBOW,
            self.RIGHT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):

            angle = self._calculate_angle(
                landmarks[self.RIGHT_SHOULDER],
                landmarks[self.RIGHT_ELBOW],
                landmarks[self.RIGHT_WRIST],
            )

            candidates.append(
                ("right", angle)
            )

        left_indexes = (
            self.LEFT_SHOULDER,
            self.LEFT_ELBOW,
            self.LEFT_WRIST,
        )

        if self._has_valid_landmarks(
            landmarks,
            left_indexes,
        ):

            angle = self._calculate_angle(
                landmarks[self.LEFT_SHOULDER],
                landmarks[self.LEFT_ELBOW],
                landmarks[self.LEFT_WRIST],
            )

            candidates.append(
                ("left", angle)
            )

        return candidates

    def _detect_bicep_curl(self, landmarks):

        candidates = self._get_arm_angles(
            landmarks
        )

        if not candidates:
            return None, 0.0, None

        candidates.sort(
            key=lambda item: item[1]
        )

        side, angle = candidates[0]

        # If the best arm isn't actually bent,
        # it isn't a curl.
        if angle > self.BICEP_CURL_THRESHOLD:
            return None, 0.0, None

        # If both arms are bent almost equally,
        # avoid aggressively calling it a curl.
        if len(candidates) >= 2:

            second_angle = candidates[1][1]

            advantage = (
                second_angle - angle
            )

            if advantage < self.BICEP_SIDE_ADVANTAGE:

                # Both arms can legitimately be bent,
                # but detection confidence should be lower.
                confidence = 0.72

            else:
                confidence = 0.82

        else:
            confidence = 0.78

        # Deeper curl -> higher confidence.
        if angle <= 90:
            confidence += 0.10

        elif angle <= 105:
            confidence += 0.05

        confidence = min(
            0.96,
            confidence,
        )

        return (
            "bicep_curl",
            round(confidence, 2),
            side,
        )

    # ==========================================================
    # LEG ANGLES
    # ==========================================================

    def _get_leg_angles(self, landmarks):

        right_angle = None
        left_angle = None

        right_indexes = (
            self.RIGHT_HIP,
            self.RIGHT_KNEE,
            self.RIGHT_ANKLE,
        )

        if self._has_valid_landmarks(
            landmarks,
            right_indexes,
        ):

            right_angle = self._calculate_angle(
                landmarks[self.RIGHT_HIP],
                landmarks[self.RIGHT_KNEE],
                landmarks[self.RIGHT_ANKLE],
            )

        left_indexes = (
            self.LEFT_HIP,
            self.LEFT_KNEE,
            self.LEFT_ANKLE,
        )

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
    # SQUAT / LUNGE
    # ==========================================================

    def _detect_leg_exercise(self, landmarks):

        right_angle, left_angle = (
            self._get_leg_angles(landmarks)
        )

        if (
            right_angle is None
            and left_angle is None
        ):
            return None, 0.0, None

        # ------------------------------------------------------
        # BOTH LEGS
        # ------------------------------------------------------

        if (
            right_angle is not None
            and left_angle is not None
        ):

            difference = abs(
                right_angle - left_angle
            )

            right_bent = (
                right_angle <= self.LEG_BENT_THRESHOLD
            )

            left_bent = (
                left_angle <= self.LEG_BENT_THRESHOLD
            )

            # ==================================================
            # SQUAT
            # ==================================================

            if (
                right_bent
                and left_bent
                and difference <= self.LUNGE_ANGLE_DIFFERENCE
            ):

                confidence = 0.82

                if (
                    right_angle <= self.DEEP_SQUAT_THRESHOLD
                    and left_angle <= self.DEEP_SQUAT_THRESHOLD
                ):
                    confidence = 0.92

                elif (
                    right_angle <= 115
                    and left_angle <= 115
                ):
                    confidence = 0.87

                side = "right" if right_angle <= left_angle else "left"

                return (
                    "squat",
                    confidence,
                    side,
                )

            # ==================================================
            # LUNGE
            # ==================================================

            if (
                right_bent
                and (
                    not left_bent
                    or difference > self.LUNGE_ANGLE_DIFFERENCE
                )
            ):

                confidence = 0.82

                if right_angle < 105:
                    confidence = 0.88

                return (
                    "lunge",
                    confidence,
                    "right",
                )

            if (
                left_bent
                and (
                    not right_bent
                    or difference > self.LUNGE_ANGLE_DIFFERENCE
                )
            ):

                confidence = 0.82

                if left_angle < 105:
                    confidence = 0.88

                return (
                    "lunge",
                    confidence,
                    "left",
                )

        # ------------------------------------------------------
        # ONE LEG
        # ------------------------------------------------------

        # Do NOT aggressively classify one visible bent leg
        # as a lunge. This was one source of false detection.
        #
        # We require a stronger bend.

        if right_angle is not None:

            if right_angle <= 105:
                return (
                    "lunge",
                    0.72,
                    "right",
                )

        if left_angle is not None:

            if left_angle <= 105:
                return (
                    "lunge",
                    0.72,
                    "left",
                )

        return None, 0.0, None

    # ==========================================================
    # RAW DETECTION
    # ==========================================================

    def _detect_raw(self, landmarks):

        # Bicep curl first.
        #
        # Important:
        # Only a clearly bent arm should trigger this.
        exercise, confidence, side = (
            self._detect_bicep_curl(
                landmarks
            )
        )

        if exercise is not None:
            return exercise, confidence, side

        return self._detect_leg_exercise(
            landmarks
        )

    # ==========================================================
    # TEMPORAL STABILIZATION
    # ==========================================================

    def _stabilize(
        self,
        exercise,
        confidence,
        side,
    ):

        # ------------------------------------------------------
        # No current detection
        # ------------------------------------------------------

        if self.current_exercise is None:

            if exercise is None:

                self.pending_exercise = None
                self.pending_side = None
                self.pending_count = 0

                return self._empty_result()

            if exercise == self.pending_exercise:

                self.pending_count += 1

            else:

                self.pending_exercise = exercise
                self.pending_side = side
                self.pending_count = 1

            if (
                self.pending_count
                >= self.confirmation_frames
            ):

                self.current_exercise = exercise
                self.current_confidence = confidence
                self.current_side = side

                self.pending_exercise = None
                self.pending_side = None
                self.pending_count = 0

                return self._set_result(
                    exercise,
                    confidence,
                    side,
                )

            return self._empty_result()

        # ------------------------------------------------------
        # Same exercise
        # ------------------------------------------------------

        if exercise == self.current_exercise:

            self.stable_match_count += 1

            self.current_confidence = (
                0.80 * self.current_confidence
                + 0.20 * confidence
            )

            if side is not None:
                self.current_side = side

            self.pending_exercise = None
            self.pending_side = None
            self.pending_count = 0

            return self._set_result(
                self.current_exercise,
                self.current_confidence,
                self.current_side,
            )

        # ------------------------------------------------------
        # Different exercise
        # ------------------------------------------------------

        if exercise is None:

            self.stable_match_count = 0

            # Keep current exercise temporarily.
            # This prevents one bad frame from switching
            # the workout to nothing.
            return self._set_result(
                self.current_exercise,
                self.current_confidence,
                self.current_side,
            )

        if exercise == self.pending_exercise:

            self.pending_count += 1

        else:

            self.pending_exercise = exercise
            self.pending_side = side
            self.pending_count = 1

        # Require confirmation before switching.
        if (
            self.pending_count
            >= self.confirmation_frames
        ):

            self.current_exercise = exercise
            self.current_confidence = confidence
            self.current_side = side

            self.pending_exercise = None
            self.pending_side = None
            self.pending_count = 0
            self.stable_match_count = 0

            return self._set_result(
                exercise,
                confidence,
                side,
            )

        # Keep existing exercise during transition.
        return self._set_result(
            self.current_exercise,
            self.current_confidence,
            self.current_side,
        )

    # ==========================================================
    # MAIN DETECTION
    # ==========================================================

    def detect(self, landmarks):

        if landmarks is None:
            return self._stabilize(
                None,
                0.0,
                None,
            )

        try:
            if len(landmarks) < self.REQUIRED_LANDMARK_COUNT:
                return self._stabilize(
                    None,
                    0.0,
                    None,
                )

        except (TypeError, ValueError):
            return self._empty_result()

        if not self._has_valid_pose(landmarks):

            return self._stabilize(
                None,
                0.0,
                None,
            )

        exercise, confidence, side = (
            self._detect_raw(landmarks)
        )

        self.detection_history.append(
            exercise
        )

        return self._stabilize(
            exercise,
            confidence,
            side,
        )

    # ==========================================================
    # RESULT HELPERS
    # ==========================================================

    def _set_result(
        self,
        exercise,
        confidence,
        side,
    ):

        self.current_exercise = exercise
        self.current_confidence = float(
            confidence
        )
        self.current_side = side

        return {
            "exercise": exercise,
            "confidence": round(
                float(confidence),
                2,
            ),
            "side": side,
        }

    def _empty_result(self):

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

    def get_current_side(self):
        return self.current_side

    # ==========================================================
    # RESET
    # ==========================================================

    def reset(self):

        self.current_exercise = None
        self.current_confidence = 0.0
        self.current_side = None

        self.detection_history.clear()

        self.pending_exercise = None
        self.pending_side = None
        self.pending_count = 0

        self.stable_match_count = 0
